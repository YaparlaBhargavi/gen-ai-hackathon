# app/agents/calendar_agent.py
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models import CalendarEvent, OAuthToken
import re
import logging

logger = logging.getLogger(__name__)


class CalendarAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session

    async def process_calendar_query(self, query: str) -> Dict[str, Any]:
        """Process calendar-related queries"""
        query_lower = query.lower()

        if any(
            keyword in query_lower for keyword in ["add", "create", "new", "schedule"]
        ):
            return await self.create_event(query)
        elif any(
            keyword in query_lower
            for keyword in [
                "list",
                "show",
                "view",
                "today",
                "tomorrow",
                "week",
                "month",
            ]
        ):
            return await self.list_events(query)
        elif any(keyword in query_lower for keyword in ["delete", "remove", "cancel"]):
            return await self.delete_event(query)
        elif any(keyword in query_lower for keyword in ["update", "edit", "change"]):
            return await self.update_event(query)
        elif any(keyword in query_lower for keyword in ["sync", "connect"]):
            return await self.get_sync_status()
        else:
            return await self.get_calendar_summary()

    async def create_event(self, query: str) -> Dict[str, Any]:
        """Create calendar event from natural language"""
        # Extract title
        title_match = re.search(
            r"(?:meeting|event|appointment)[:\s]+(.+?)(?:at|on|tomorrow|today|$)",
            query,
            re.IGNORECASE,
        )
        title = title_match.group(1).strip() if title_match else "Event"

        # Parse date and time
        start_time = None
        today = datetime.now()

        # Check for date keywords
        if "tomorrow" in query.lower():
            base_date = today + timedelta(days=1)
        elif "next week" in query.lower():
            base_date = today + timedelta(days=7)
        elif "next month" in query.lower():
            base_date = today + timedelta(days=30)
        else:
            base_date = today

        # Parse time
        time_match = re.search(
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", query, re.IGNORECASE
        )
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3).lower()

            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

            start_time = base_date.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
        else:
            # Default to 2 PM if no time specified
            start_time = base_date.replace(hour=14, minute=0, second=0, microsecond=0)

        # Check for all-day event
        all_day = "all day" in query.lower() or "all-day" in query.lower()

        # Set end time
        if all_day:
            end_time = start_time + timedelta(days=1) - timedelta(seconds=1)
        else:
            end_time = start_time + timedelta(hours=1)

            # Parse duration
            duration_match = re.search(
                r"for\s+(\d+)\s+(hour|hr|minute|min)", query, re.IGNORECASE
            )
            if duration_match:
                duration_num = int(duration_match.group(1))
                duration_unit = duration_match.group(2).lower()
                if "hour" in duration_unit or "hr" in duration_unit:
                    end_time = start_time + timedelta(hours=duration_num)
                elif "minute" in duration_unit or "min" in duration_unit:
                    end_time = start_time + timedelta(minutes=duration_num)

        # Extract description
        description = None
        desc_match = re.search(r"about\s+(.+?)(?:at|on|for|$)", query, re.IGNORECASE)
        if desc_match:
            description = desc_match.group(1).strip()

        # Extract location
        location = None
        loc_match = re.search(r"at\s+(.+?)(?:about|for|$)", query, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip()

        # Extract reminder time
        reminder_minutes = 30
        reminder_match = re.search(
            r"remind\s+(\d+)\s+(minute|hour)s?", query, re.IGNORECASE
        )
        if reminder_match:
            reminder_num = int(reminder_match.group(1))
            reminder_unit = reminder_match.group(2).lower()
            if "hour" in reminder_unit:
                reminder_minutes = reminder_num * 60
            else:
                reminder_minutes = reminder_num

        # Extract recurrence
        recurrence = None
        recurrence_end = None
        if "daily" in query.lower():
            recurrence = "daily"
        elif "weekly" in query.lower():
            recurrence = "weekly"
        elif "monthly" in query.lower():
            recurrence = "monthly"

        # Parse recurrence end
        recurrence_end_match = re.search(r"until\s+(.+?)(?:$)", query, re.IGNORECASE)
        if recurrence_end_match:
            try:
                recurrence_end = datetime.strptime(
                    recurrence_end_match.group(1).strip(), "%B %d, %Y"
                )
            except ValueError:
                # If date parsing fails, log and continue without recurrence end
                logger.warning(
                    f"Failed to parse recurrence end date: {recurrence_end_match.group(1)}"
                )

        event = CalendarEvent(
            user_id=self.user_id,
            title=title[:200],
            description=description,
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
            location=location,
            reminder_minutes=reminder_minutes,
            reminder_sent=False,
            recurrence=recurrence,
            recurrence_end=recurrence_end,
            created_at=datetime.utcnow(),
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        response = f"📅 Event added: '{title}'"
        if all_day:
            response += f"\n📅 {start_time.strftime('%A, %B %d')} (All day)"
        else:
            response += f"\n🕒 {start_time.strftime('%A, %B %d at %I:%M %p')}"
            if end_time:
                response += f" → {end_time.strftime('%I:%M %p')}"
        if location:
            response += f"\n📍 Location: {location}"
        if reminder_minutes != 30:
            response += f"\n⏰ Reminder: {reminder_minutes} minutes before"
        if recurrence:
            response += f"\n🔄 Repeats: {recurrence.capitalize()}"
        if recurrence_end:
            response += f" until {recurrence_end.strftime('%B %d, %Y')}"

        return {
            "status": "success",
            "response": response,
            "event": {
                "id": event.id,
                "title": event.title,
                "start": event.start_time.isoformat(),
                "end": event.end_time.isoformat() if event.end_time else None,
                "all_day": event.all_day,
                "location": event.location,
                "recurrence": event.recurrence,
            },
        }

    async def list_events(self, query: str) -> Dict[str, Any]:
        """List calendar events"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if "today" in query.lower():
            start_date = today
            end_date = today + timedelta(days=1)
            period = "Today"
        elif "tomorrow" in query.lower():
            start_date = today + timedelta(days=1)
            end_date = today + timedelta(days=2)
            period = "Tomorrow"
        elif "week" in query.lower() or "this week" in query.lower():
            start_date = today
            end_date = today + timedelta(days=7)
            period = "This Week"
        elif "next week" in query.lower():
            start_date = today + timedelta(days=7)
            end_date = today + timedelta(days=14)
            period = "Next Week"
        elif "month" in query.lower() or "this month" in query.lower():
            start_date = today.replace(day=1)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1, day=1)
            period = "This Month"
        else:
            start_date = today
            end_date = today + timedelta(days=7)
            period = "Upcoming"

        events = (
            self.db.query(CalendarEvent)
            .filter(
                CalendarEvent.user_id == self.user_id,
                CalendarEvent.start_time >= start_date,
                CalendarEvent.start_time <= end_date,
            )
            .order_by(CalendarEvent.start_time)
            .all()
        )

        if not events:
            return {
                "status": "success",
                "response": f"📅 No events scheduled for {period.lower()}.",
            }

        event_list = []
        for event in events:
            if event.all_day:
                date_str = event.start_time.strftime("%A, %B %d")
                time_str = "(All day)"
                end_str = ""
            else:
                date_str = event.start_time.strftime("%A, %B %d")
                time_str = event.start_time.strftime("%I:%M %p")
                end_str = (
                    f" - {event.end_time.strftime('%I:%M %p')}"
                    if event.end_time
                    else ""
                )
            location_str = f" @ {event.location}" if event.location else ""
            sync_str = ""
            if event.external_calendar_id:
                sync_str = f" 🔄 Synced to {event.external_calendar_type}"
            event_list.append(
                f"• {date_str} at {time_str}{end_str}: {event.title}{location_str}{sync_str}"
            )

        response = f"📅 {period} Events:\n\n" + "\n".join(event_list)

        return {
            "status": "success",
            "response": response,
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "start": e.start_time.isoformat(),
                    "end": e.end_time.isoformat() if e.end_time else None,
                    "all_day": e.all_day,
                    "location": e.location,
                    "synced": bool(e.external_calendar_id),
                    "sync_type": e.external_calendar_type,
                }
                for e in events
            ],
        }

    async def delete_event(self, query: str) -> Dict[str, Any]:
        """Delete calendar event"""
        event_id_match = re.search(r"(\d+)", query)
        if event_id_match:
            event_id = int(event_id_match.group(1))
            event = (
                self.db.query(CalendarEvent)
                .filter(
                    CalendarEvent.id == event_id, CalendarEvent.user_id == self.user_id
                )
                .first()
            )

            if event:
                title = event.title
                self.db.delete(event)
                self.db.commit()
                return {"status": "success", "response": f"🗑️ Event deleted: '{title}'"}

        # Try to find by title
        title_match = re.search(
            r"delete\s+event\s+['\"]?(.+?)['\"]?$", query, re.IGNORECASE
        )
        if title_match:
            title = title_match.group(1).strip()
            event = (
                self.db.query(CalendarEvent)
                .filter(
                    CalendarEvent.user_id == self.user_id,
                    CalendarEvent.title.ilike(f"%{title}%"),
                )
                .first()
            )
            if event:
                self.db.delete(event)
                self.db.commit()
                return {
                    "status": "success",
                    "response": f"🗑️ Event deleted: '{event.title}'",
                }

        return {
            "status": "error",
            "message": "Event not found. Please provide a valid event ID or title.",
        }

    async def update_event(self, query: str) -> Dict[str, Any]:
        """Update calendar event"""
        # Extract event ID
        event_id_match = re.search(r"(\d+)", query)
        if not event_id_match:
            return {
                "status": "error",
                "message": "Please specify event ID (e.g., 'Update event #1 to tomorrow at 3pm')",
            }

        event_id = int(event_id_match.group(1))
        event = (
            self.db.query(CalendarEvent)
            .filter(CalendarEvent.id == event_id, CalendarEvent.user_id == self.user_id)
            .first()
        )

        if not event:
            return {"status": "error", "message": "Event not found"}

        updates = []
        needs_resync = False

        # Update time
        if "tomorrow" in query.lower():
            new_time = datetime.now() + timedelta(days=1)
            time_match = re.search(
                r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", query, re.IGNORECASE
            )
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                ampm = time_match.group(3).lower()

                if ampm == "pm" and hour != 12:
                    hour += 12
                elif ampm == "am" and hour == 12:
                    hour = 0

                new_time = new_time.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

            event.start_time = new_time
            if event.end_time:
                duration = event.end_time - event.start_time
                event.end_time = new_time + duration
            event.all_day = False
            updates.append(f"time to {new_time.strftime('%A, %B %d at %I:%M %p')}")
            needs_resync = True

        # Update title
        title_match = re.search(r"title\s+to\s+['\"]?(.+?)['\"]?", query, re.IGNORECASE)
        if title_match:
            new_title = title_match.group(1).strip()
            event.title = new_title[:200]
            updates.append(f"title to '{new_title}'")
            needs_resync = True

        # Update location
        location_match = re.search(
            r"location\s+to\s+['\"]?(.+?)['\"]?", query, re.IGNORECASE
        )
        if location_match:
            new_location = location_match.group(1).strip()
            event.location = new_location
            updates.append(f"location to '{new_location}'")
            needs_resync = True

        # Mark that event needs resync if it was synced before
        if needs_resync and event.external_calendar_id:
            event.last_synced_at = None  # Mark for resync

        self.db.commit()

        if updates:
            response = f"✅ Event updated: {', '.join(updates)}"
            if needs_resync and event.external_calendar_id:
                response += "\n⚠️ This event will be resynced with your email calendar"
            return {
                "status": "success",
                "response": response,
            }

        return {"status": "error", "message": "No valid updates specified"}

    async def get_calendar_summary(self) -> Dict[str, Any]:
        """Get calendar summary"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=7)

        events = (
            self.db.query(CalendarEvent)
            .filter(
                CalendarEvent.user_id == self.user_id,
                CalendarEvent.start_time >= week_start,
                CalendarEvent.start_time <= week_end,
            )
            .all()
        )

        today_events = [e for e in events if e.start_time.date() == today.date()]
        week_events = [e for e in events if e.start_time.date() != today.date()]

        # Get synced events count
        synced_events = [e for e in events if e.external_calendar_id]

        response = "📅 Calendar Summary:\n\n"
        response += f"🎯 Today: {len(today_events)} event(s)\n"
        response += f"📆 This Week: {len(week_events)} event(s)\n"
        response += f"📊 Total: {len(events)} event(s) this week\n"
        response += f"🔄 Synced with Email Calendar: {len(synced_events)} event(s)\n"

        if today_events:
            response += "\n📍 Today's Events:\n"
            for event in today_events[:3]:
                if event.all_day:
                    response += f"   • {event.title} (All day)"
                else:
                    time_str = event.start_time.strftime("%I:%M %p")
                    response += f"   • {time_str} - {event.title}"
                if event.external_calendar_id:
                    response += f" [Synced to {event.external_calendar_type}]"
                response += "\n"

        # Get upcoming events for next 7 days
        upcoming = (
            self.db.query(CalendarEvent)
            .filter(
                CalendarEvent.user_id == self.user_id,
                CalendarEvent.start_time >= today,
                CalendarEvent.start_time <= today + timedelta(days=7),
            )
            .order_by(CalendarEvent.start_time)
            .limit(5)
            .all()
        )

        if upcoming:
            response += "\n⏰ Upcoming Events (Next 7 Days):\n"
            for event in upcoming:
                if event.start_time.date() == today.date():
                    day_str = "Today"
                elif event.start_time.date() == (today + timedelta(days=1)).date():
                    day_str = "Tomorrow"
                else:
                    day_str = event.start_time.strftime("%a, %b %d")

                if event.all_day:
                    response += f"   • {day_str}: {event.title} (All day)"
                else:
                    time_str = event.start_time.strftime("%I:%M %p")
                    response += f"   • {day_str} at {time_str}: {event.title}"
                if event.external_calendar_id:
                    response += " [Synced]"
                response += "\n"

        return {
            "status": "success",
            "response": response,
            "summary": {
                "today_events": len(today_events),
                "week_events": len(week_events),
                "total_events": len(events),
                "upcoming_events": len(upcoming),
                "synced_events": len(synced_events),
            },
        }

    async def create_event_from_form(
        self,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        all_day: bool = False,
        location: Optional[str] = None,
        description: Optional[str] = None,
        reminder_minutes: int = 30,
        recurrence: Optional[str] = None,
        recurrence_end: Optional[datetime] = None,
        sync_with_calendar: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create calendar event from form data"""
        try:
            if end_time is None:
                if all_day:
                    end_time = start_time + timedelta(days=1) - timedelta(seconds=1)
                else:
                    end_time = start_time + timedelta(hours=1)

            event = CalendarEvent(
                user_id=self.user_id,
                title=title[:200],
                description=description,
                start_time=start_time,
                end_time=end_time,
                all_day=all_day,
                location=location,
                reminder_minutes=reminder_minutes,
                reminder_sent=False,
                recurrence=recurrence,
                recurrence_end=recurrence_end,
                created_at=datetime.utcnow(),
            )

            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)

            result = {
                "status": "success",
                "message": "Event created successfully",
                "event": {
                    "id": event.id,
                    "title": event.title,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat() if event.end_time else None,
                    "all_day": event.all_day,
                    "location": event.location,
                },
            }

            # If sync requested, return sync info
            if sync_with_calendar:
                result["sync_requested"] = sync_with_calendar
                result["message"] = (
                    "Event created and will be synced with your email calendar"
                )

            return result
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating event: {e}")
            return {"status": "error", "message": str(e)}

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get calendar sync status"""
        # Get connected calendars
        tokens = (
            self.db.query(OAuthToken).filter(OAuthToken.user_id == self.user_id).all()
        )

        connected_calendars = []
        for token in tokens:
            expires_in = None
            if token.expires_at:
                expires_in = (token.expires_at - datetime.utcnow()).total_seconds()

            connected_calendars.append(
                {
                    "provider": token.provider,
                    "connected": True,
                    "expires_in": expires_in if expires_in and expires_in > 0 else None,
                    "calendar_id": token.calendar_id,
                }
            )

        # Get synced events count
        synced_events = (
            self.db.query(CalendarEvent)
            .filter(
                CalendarEvent.user_id == self.user_id,
                CalendarEvent.external_calendar_id.isnot(None),
            )
            .count()
        )

        response_lines = ["📧 Email Calendar Connection Status:", ""]
        if connected_calendars:
            for cal in connected_calendars:
                response_lines.append(
                    f"✅ {cal['provider'].capitalize()} Calendar: Connected"
                )
                if cal["expires_in"]:
                    response_lines.append(
                        f"   Token expires in: {int(cal['expires_in'] / 60)} minutes"
                    )
        else:
            response_lines.append("❌ No email calendars connected")
            response_lines.append(
                "   Connect your Google or Outlook calendar to sync events"
            )

        response_lines.append(
            f"\n📊 Synced Events: {synced_events} event(s) synced with email calendar"
        )

        response = "\n".join(response_lines)

        return {
            "status": "success",
            "response": response,
            "connected_calendars": connected_calendars,
            "synced_events_count": synced_events,
        }

    async def mark_event_synced(
        self, event_id: int, external_id: str, provider: str
    ) -> bool:
        """Mark an event as synced with external calendar"""
        try:
            event = (
                self.db.query(CalendarEvent)
                .filter(
                    CalendarEvent.id == event_id, CalendarEvent.user_id == self.user_id
                )
                .first()
            )

            if event:
                event.external_calendar_id = external_id
                event.external_calendar_type = provider
                event.last_synced_at = datetime.utcnow()
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error marking event as synced: {e}")
            return False
