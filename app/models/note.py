'''app/models/note.py - Pydantic note models'''
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NoteCreate(BaseModel):
    title: str
    content: str
    tags: Optional[str] = None

class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    tags: Optional[str] = None
    created_at: datetime

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None

