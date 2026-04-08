# app/models/calendar.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CalendarEventCreate(BaseModel):
    """Schema for creating a calendar event"""

    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    all_day: bool = False
    location: Optional[str] = None
    color: Optional[str] = None
    reminder_minutes: int = 30
    recurrence: Optional[str] = None
    recurrence_end: Optional[datetime] = None


class CalendarEventResponse(BaseModel):
    """Schema for calendar event response"""

    id: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    all_day: bool
    location: Optional[str] = None
    color: Optional[str] = None
    reminder_minutes: int
    reminder_sent: bool
    recurrence: Optional[str] = None
    recurrence_end: Optional[datetime] = None
    created_at: datetime


class CalendarEventUpdate(BaseModel):
    """Schema for updating a calendar event"""

    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    location: Optional[str] = None
    color: Optional[str] = None
    reminder_minutes: Optional[int] = None
    recurrence: Optional[str] = None
    recurrence_end: Optional[datetime] = None


class CalendarEventListResponse(BaseModel):
    """Schema for calendar event list response"""

    events: List[CalendarEventResponse]
    total: int
    limit: int
    skip: int
