'''app/models/task.py - Pydantic task models'''
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    urgency: Optional[str] = 'normal'

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    urgency: str
    created_at: datetime

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    urgency: Optional[str] = None

