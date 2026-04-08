# app/models/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""

    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    theme: str = "dark"


class UserLogin(BaseModel):
    """Schema for user login"""

    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""

    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    timezone: str
    language: str
    theme: str
    email_notifications: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool


class UserUpdate(BaseModel):
    """Schema for updating user profile"""

    full_name: Optional[str] = None
    avatar: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None
    email_notifications: Optional[bool] = None


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""

    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    timezone: str
    language: str
    theme: str
    email_notifications: bool
    created_at: datetime
    last_login: Optional[datetime] = None
