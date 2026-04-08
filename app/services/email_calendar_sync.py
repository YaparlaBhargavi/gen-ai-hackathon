# app/services/email_calendar_sync.py
from sqlalchemy.orm import Session
import httpx
from typing import Optional
from datetime import datetime, timedelta
import logging
from app.database.models import CalendarEvent, OAuthToken

logger = logging.getLogger(__name__)


class EmailCalendarSync:
    """Service to sync events with external email calendars"""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def sync_to_google_calendar(self, user_id: int, event: CalendarEvent) -> bool:
        """Sync event to Google Calendar"""
        try:
            # Get user's Google Calendar credentials
            token = (
                self.db.query(OAuthToken)
                .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "google")
                .first()
            )

            if not token:
                logger.warning(f"No Google Calendar token found for user {user_id}")
                return False

            # Check if token is expired and refresh if needed
            if token.expires_at and token.expires_at <= datetime.utcnow():
                # Token expired, would need refresh logic here
                logger.warning(f"Google token expired for user {user_id}")
                return False

            # Prepare event data for Google Calendar API
            google_event = {
                "summary": event.title,
                "description": event.description or "",
                "location": event.location or "",
                "start": {"dateTime": event.start_time.isoformat(), "timeZone": "UTC"},
                "end": {
                    "dateTime": (
                        event.end_time or event.start_time + timedelta(hours=1)
                    ).isoformat(),
                    "timeZone": "UTC",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": event.reminder_minutes or 30},
                        {"method": "popup", "minutes": event.reminder_minutes or 30},
                    ],
                },
            }

            # Handle all-day events
            if event.all_day:
                google_event["start"] = {"date": event.start_time.date().isoformat()}
                google_event["end"] = {
                    "date": (event.end_time or event.start_time + timedelta(days=1))
                    .date()
                    .isoformat()
                }

            # Make API call to Google Calendar
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers={
                        "Authorization": f"Bearer {token.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=google_event,
                )

                if response.status_code == 200:
                    # Store the Google Calendar event ID
                    event_data = response.json()
                    event.external_calendar_id = event_data.get("id")
                    event.external_calendar_type = "google"
                    event.last_synced_at = datetime.utcnow()
                    self.db.commit()
                    logger.info(f"Event {event.id} synced to Google Calendar")
                    return True
                else:
                    logger.error(f"Google Calendar API error: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error syncing to Google Calendar: {e}")
            return False

    async def sync_to_outlook_calendar(
        self, user_id: int, event: CalendarEvent
    ) -> bool:
        """Sync event to Outlook Calendar"""
        try:
            # Get user's Outlook credentials
            token = (
                self.db.query(OAuthToken)
                .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "outlook")
                .first()
            )

            if not token:
                logger.warning(f"No Outlook Calendar token found for user {user_id}")
                return False

            # Check if token is expired and refresh if needed
            if token.expires_at and token.expires_at <= datetime.utcnow():
                # Token expired, would need refresh logic here
                logger.warning(f"Outlook token expired for user {user_id}")
                return False

            # Prepare event data for Outlook Calendar API
            outlook_event = {
                "subject": event.title,
                "body": {"contentType": "HTML", "content": event.description or ""},
                "start": {"dateTime": event.start_time.isoformat(), "timeZone": "UTC"},
                "end": {
                    "dateTime": (
                        event.end_time or event.start_time + timedelta(hours=1)
                    ).isoformat(),
                    "timeZone": "UTC",
                },
                "location": {"displayName": event.location or ""},
                "isReminderOn": True,
                "reminderMinutesBeforeStart": event.reminder_minutes or 30,
            }

            # Handle all-day events
            if event.all_day:
                outlook_event["isAllDay"] = True
                outlook_event["start"]["dateTime"] = event.start_time.date().isoformat()
                outlook_event["end"]["dateTime"] = (
                    (event.end_time or event.start_time + timedelta(days=1))
                    .date()
                    .isoformat()
                )

            # Make API call to Outlook Calendar
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://graph.microsoft.com/v1.0/me/events",
                    headers={
                        "Authorization": f"Bearer {token.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=outlook_event,
                )

                if response.status_code == 201:
                    # Store the Outlook event ID
                    event_data = response.json()
                    event.external_calendar_id = event_data.get("id")
                    event.external_calendar_type = "outlook"
                    event.last_synced_at = datetime.utcnow()
                    self.db.commit()
                    logger.info(f"Event {event.id} synced to Outlook Calendar")
                    return True
                else:
                    logger.error(f"Outlook Calendar API error: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error syncing to Outlook Calendar: {e}")
            return False

    async def update_google_event(self, user_id: int, event: CalendarEvent) -> bool:
        """Update existing Google Calendar event"""
        if not event.external_calendar_id or event.external_calendar_type != "google":
            return await self.sync_to_google_calendar(user_id, event)

        try:
            token = (
                self.db.query(OAuthToken)
                .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "google")
                .first()
            )

            if not token:
                return False

            # Prepare update data
            google_event = {
                "summary": event.title,
                "description": event.description or "",
                "location": event.location or "",
                "start": {"dateTime": event.start_time.isoformat(), "timeZone": "UTC"},
                "end": {
                    "dateTime": (
                        event.end_time or event.start_time + timedelta(hours=1)
                    ).isoformat(),
                    "timeZone": "UTC",
                },
            }

            if event.all_day:
                google_event["start"] = {"date": event.start_time.date().isoformat()}
                google_event["end"] = {
                    "date": (event.end_time or event.start_time + timedelta(days=1))
                    .date()
                    .isoformat()
                }

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event.external_calendar_id}",
                    headers={
                        "Authorization": f"Bearer {token.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=google_event,
                )

                if response.status_code == 200:
                    event.last_synced_at = datetime.utcnow()
                    self.db.commit()
                    return True
                else:
                    logger.error(
                        f"Error updating Google Calendar event: {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {e}")
            return False

    async def update_outlook_event(self, user_id: int, event: CalendarEvent) -> bool:
        """Update existing Outlook Calendar event"""
        if not event.external_calendar_id or event.external_calendar_type != "outlook":
            return await self.sync_to_outlook_calendar(user_id, event)

        try:
            token = (
                self.db.query(OAuthToken)
                .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "outlook")
                .first()
            )

            if not token:
                return False

            # Prepare update data
            outlook_event = {
                "subject": event.title,
                "body": {"contentType": "HTML", "content": event.description or ""},
                "start": {"dateTime": event.start_time.isoformat(), "timeZone": "UTC"},
                "end": {
                    "dateTime": (
                        event.end_time or event.start_time + timedelta(hours=1)
                    ).isoformat(),
                    "timeZone": "UTC",
                },
                "location": {"displayName": event.location or ""},
                "isReminderOn": True,
                "reminderMinutesBeforeStart": event.reminder_minutes or 30,
            }

            if event.all_day:
                outlook_event["isAllDay"] = True
                outlook_event["start"]["dateTime"] = event.start_time.date().isoformat()
                outlook_event["end"]["dateTime"] = (
                    (event.end_time or event.start_time + timedelta(days=1))
                    .date()
                    .isoformat()
                )

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://graph.microsoft.com/v1.0/me/events/{event.external_calendar_id}",
                    headers={
                        "Authorization": f"Bearer {token.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=outlook_event,
                )

                if response.status_code == 200:
                    event.last_synced_at = datetime.utcnow()
                    self.db.commit()
                    return True
                else:
                    logger.error(
                        f"Error updating Outlook Calendar event: {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error updating Outlook Calendar event: {e}")
            return False

    async def delete_google_event(self, user_id: int, event: CalendarEvent) -> bool:
        """Delete event from Google Calendar"""
        if not event.external_calendar_id:
            return True

        try:
            token = (
                self.db.query(OAuthToken)
                .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "google")
                .first()
            )

            if not token:
                return False

            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event.external_calendar_id}",
                    headers={"Authorization": f"Bearer {token.access_token}"},
                )

                if response.status_code == 204:
                    logger.info(f"Event {event.id} deleted from Google Calendar")
                    return True
                else:
                    logger.error(
                        f"Error deleting from Google Calendar: {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {e}")
            return False

    async def delete_outlook_event(self, user_id: int, event: CalendarEvent) -> bool:
        """Delete event from Outlook Calendar"""
        if not event.external_calendar_id:
            return True

        try:
            token = (
                self.db.query(OAuthToken)
                .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "outlook")
                .first()
            )

            if not token:
                return False

            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"https://graph.microsoft.com/v1.0/me/events/{event.external_calendar_id}",
                    headers={"Authorization": f"Bearer {token.access_token}"},
                )

                if response.status_code == 204:
                    logger.info(f"Event {event.id} deleted from Outlook Calendar")
                    return True
                else:
                    logger.error(
                        f"Error deleting from Outlook Calendar: {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error deleting Outlook Calendar event: {e}")
            return False

    async def get_google_access_token(self, user_id: int) -> Optional[str]:
        """Retrieve user's Google Calendar access token"""
        token = (
            self.db.query(OAuthToken)
            .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "google")
            .first()
        )

        if token:
            # Check if token is expired
            if token.expires_at and token.expires_at <= datetime.utcnow():
                # Token expired, would need refresh logic
                return None
            return token.access_token
        return None

    async def get_outlook_access_token(self, user_id: int) -> Optional[str]:
        """Retrieve user's Outlook access token"""
        token = (
            self.db.query(OAuthToken)
            .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "outlook")
            .first()
        )

        if token:
            # Check if token is expired
            if token.expires_at and token.expires_at <= datetime.utcnow():
                # Token expired, would need refresh logic
                return None
            return token.access_token
        return None
