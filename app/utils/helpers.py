# app/utils/helpers.py
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


def extract_dates(text: str) -> List[datetime]:
    """Extract dates from text"""
    dates = []

    # Look for patterns like "tomorrow", "next week", etc.
    now = datetime.now()

    if "tomorrow" in text.lower():
        dates.append(now + timedelta(days=1))
    if "next week" in text.lower():
        dates.append(now + timedelta(days=7))
    if "next month" in text.lower():
        dates.append(now + timedelta(days=30))

    # Look for specific dates (e.g., "Jan 15", "15 Jan")
    date_patterns = [
        r"(\d{1,2})[/-](\d{1,2})",  # MM/DD or DD/MM
        r"(\w+)\s+(\d{1,2})",  # Month Day
        r"(\d{1,2})\s+(\w+)",  # Day Month
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                if len(match) == 2:
                    if match[0].isalpha():  # Month Day format
                        month_str = match[0]
                        day = int(match[1])
                        month = _get_month_number(month_str)
                        if month:
                            date = datetime(now.year, month, day)
                            if date < now:
                                date = datetime(now.year + 1, month, day)
                            dates.append(date)
                    elif match[1].isalpha():  # Day Month format
                        day = int(match[0])
                        month_str = match[1]
                        month = _get_month_number(month_str)
                        if month:
                            date = datetime(now.year, month, day)
                            if date < now:
                                date = datetime(now.year + 1, month, day)
                            dates.append(date)
                    else:  # MM/DD format
                        month = int(match[0])
                        day = int(match[1])
                        date = datetime(now.year, month, day)
                        if date < now:
                            date = datetime(now.year + 1, month, day)
                        dates.append(date)
            except (ValueError, TypeError):
                # Skip invalid date parsing
                continue

    return list(set(dates))


def _get_month_number(month_str: str) -> Optional[int]:
    """Convert month name to number"""
    months = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    # Note: 'may' is only defined once (as 5)
    return months.get(month_str.lower())


def extract_urgency(text: str) -> int:
    """Extract urgency level from text (1-10)"""
    text_lower = text.lower()

    if any(word in text_lower for word in ["critical", "urgent", "asap", "emergency"]):
        return 10
    elif "high" in text_lower:
        return 8
    elif "medium" in text_lower:
        return 5
    elif "low" in text_lower:
        return 3
    else:
        return 5


def extract_email(text: str) -> Optional[str]:
    """Extract email address from text"""
    email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
    match = re.search(email_pattern, text)
    return match.group(0) if match else None


def format_task_response(task: Any) -> Dict[str, Any]:
    """Format task object for API response"""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "urgency": task.urgency,
        "status": task.status,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "tags": task.tags if task.tags else [],
    }


def format_note_response(note: Any) -> Dict[str, Any]:
    """Format note object for API response"""
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "is_pinned": note.is_pinned,
        "color": note.color,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
        "tags": note.tags if note.tags else [],
    }


def format_calendar_event_response(event: Any) -> Dict[str, Any]:
    """Format calendar event for API response"""
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "start": event.start_time.isoformat() if event.start_time else None,
        "end": event.end_time.isoformat() if event.end_time else None,
        "allDay": event.all_day,
        "location": event.location,
        "color": event.color,
        "reminder_minutes": event.reminder_minutes,
        "recurrence": event.recurrence,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def parse_natural_language_date(text: str) -> Optional[datetime]:
    """Parse natural language date references"""
    now = datetime.now()
    text_lower = text.lower()

    if "today" in text_lower:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif "tomorrow" in text_lower:
        return (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "next week" in text_lower:
        return (now + timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "next month" in text_lower:
        return (now + timedelta(days=30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Try to parse specific time
    time_pattern = r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)"
    time_match = re.search(time_pattern, text_lower)

    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        ampm = time_match.group(3)

        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0

        date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if date < now:
            date += timedelta(days=1)
        return date

    return None


def sanitize_html(text: str) -> str:
    """Sanitize HTML content to prevent XSS"""
    import html

    return html.escape(text)


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
