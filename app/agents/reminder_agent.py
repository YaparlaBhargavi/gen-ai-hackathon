# app/agents/reminder_agent.py
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models import Task
import re


class ReminderAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session

    async def process_reminder_query(self, query: str) -> Dict[str, Any]:
        """Process reminder-related queries"""
        query_lower = query.lower()

        if "create" in query_lower or "set" in query_lower or "add" in query_lower:
            return await self.create_reminder(query)
        elif "list" in query_lower or "show" in query_lower:
            return await self.list_reminders()
        elif "delete" in query_lower or "remove" in query_lower:
            return await self.delete_reminder(query)
        else:
            return await self.get_reminder_help()

    async def create_reminder(self, query: str) -> Dict[str, Any]:
        """Create a reminder"""
        # Extract reminder text
        reminder_match = re.search(
            r"(?:reminder|remind me)[:\s]+(.+?)(?:at|in|on|$)", query, re.IGNORECASE
        )
        reminder_text = (
            reminder_match.group(1).strip() if reminder_match else "Reminder"
        )

        # Parse reminder time
        reminder_time = None
        now = datetime.now()

        if "in" in query.lower():
            # Parse relative time
            num_match = re.search(
                r"in\s+(\d+)\s+(minute|hour|day)", query, re.IGNORECASE
            )
            if num_match:
                num = int(num_match.group(1))
                unit = num_match.group(2).lower()
                if "minute" in unit:
                    reminder_time = now + timedelta(minutes=num)
                elif "hour" in unit:
                    reminder_time = now + timedelta(hours=num)
                elif "day" in unit:
                    reminder_time = now + timedelta(days=num)
        elif "at" in query.lower():
            # Parse absolute time
            time_match = re.search(
                r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)", query, re.IGNORECASE
            )
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                ampm = time_match.group(3).lower()

                if ampm == "pm" and hour != 12:
                    hour += 12
                elif ampm == "am" and hour == 12:
                    hour = 0

                reminder_time = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                if reminder_time < now:
                    reminder_time += timedelta(days=1)

        if not reminder_time:
            reminder_time = now + timedelta(hours=1)  # Default to 1 hour

        # Create a task as reminder
        task = Task(
            user_id=self.user_id,
            title=f"⏰ REMINDER: {reminder_text}",
            due_date=reminder_time,
            urgency=7,
            status="pending",
        )

        self.db.add(task)
        self.db.commit()

        return {
            "status": "success",
            "response": f"⏰ Reminder set: '{reminder_text}'\n📅 {reminder_time.strftime('%A, %B %d at %I:%M %p')}",
        }

    async def list_reminders(self) -> Dict[str, Any]:
        """List active reminders"""
        reminders = (
            self.db.query(Task)
            .filter(
                Task.user_id == self.user_id,
                Task.title.like("⏰ REMINDER:%"),
                Task.status == "pending",
                Task.due_date >= datetime.now(),
            )
            .order_by(Task.due_date)
            .all()
        )

        if not reminders:
            return {"status": "success", "response": "⏰ No active reminders."}

        reminder_list = []
        for i, r in enumerate(reminders, 1):
            time_str = r.due_date.strftime("%b %d, %I:%M %p")
            reminder_text = r.title.replace("⏰ REMINDER:", "").strip()
            reminder_list.append(f"{i}. {reminder_text} - {time_str}")

        response = "⏰ Active Reminders:\n\n" + "\n".join(reminder_list)

        return {
            "status": "success",
            "response": response,
            "reminders": [
                {"id": r.id, "text": r.title, "time": r.due_date} for r in reminders
            ],
        }

    async def delete_reminder(self, query: str) -> Dict[str, Any]:
        """Delete a reminder"""
        reminder_id_match = re.search(r"(\d+)", query)
        if reminder_id_match:
            reminder_id = int(reminder_id_match.group(1))
            reminder = (
                self.db.query(Task)
                .filter(
                    Task.id == reminder_id,
                    Task.user_id == self.user_id,
                    Task.title.like("⏰ REMINDER:%"),
                )
                .first()
            )

            if reminder:
                text = reminder.title.replace("⏰ REMINDER:", "").strip()
                self.db.delete(reminder)
                self.db.commit()
                return {
                    "status": "success",
                    "response": f"🗑️ Reminder deleted: '{text}'",
                }

        return {
            "status": "error",
            "message": "Reminder not found. Please provide a valid reminder ID.",
        }

    async def get_reminder_help(self) -> Dict[str, Any]:
        """Get reminder help"""
        help_text = "⏰ Reminder Commands:\n\n"
        help_text += "• Remind me to call mom at 3pm\n"
        help_text += "• Create reminder to take medicine in 30 minutes\n"
        help_text += "• Show my reminders\n"
        help_text += "• Delete reminder #1"

        return {"status": "success", "response": help_text}
