"""app/tools/calendar_tools.py - Calendar tool functions"""

from typing import Dict, List


def create_event(title: str, start: str, end: str, description: str = "") -> Dict:
    """Mock create calendar event"""
    event = {
        "id": len(mock_events) + 1,
        "title": title,
        "start": start,
        "end": end,
        "description": description,
    }
    mock_events.append(event)
    return event


def list_events(date: str = None) -> List[Dict]:
    """Mock list calendar events"""
    mock_events = [
        {
            "title": "Team meeting",
            "start": "2024-10-15T14:00",
            "end": "2024-10-15T15:00",
        },
        {
            "title": "Code review",
            "start": "2024-10-15T16:00",
            "end": "2024-10-15T17:00",
        },
    ]
    return mock_events


mock_events = []  # Global mock store
