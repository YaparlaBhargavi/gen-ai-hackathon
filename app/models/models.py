# app/schemas.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Basic request models
class QueryRequest(BaseModel):
    query: str


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    urgency: Optional[int] = 5
    due_date: Optional[str] = None


class NoteCreate(BaseModel):
    title: Optional[str] = "Untitled Note"
    content: str
    tags: Optional[str] = None


class ReminderCreate(BaseModel):
    message: str
    remind_at: str


# Calendar schemas
class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: str  # ISO format datetime
    end_time: str  # ISO format datetime
    location: Optional[str] = None


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None


class CalendarEventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    status: str
    google_event_id: Optional[str]
    created_at: datetime


# Database schema mappings (for response serialization)
class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    urgency: int
    due_date: Optional[datetime]
    created_at: datetime


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    tags: Optional[str]
    created_at: datetime
    updated_at: datetime


class AgentResponse(BaseModel):
    agent_name: str
    response: str
    data: Optional[dict] = None


# User schemas
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    created_at: datetime
    google_connected: bool

    class Config:
        from_attributes = True
