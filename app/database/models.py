# app/database/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    JSON,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import bcrypt

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(100))
    avatar = Column(String(200))
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    theme = Column(String(20), default="dark")
    email_notifications = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship(
        "CalendarEvent", back_populates="user", cascade="all, delete-orphan"
    )
    workflows = relationship(
        "Workflow", back_populates="user", cascade="all, delete-orphan"
    )
    email_logs = relationship(
        "EmailLog", back_populates="user", cascade="all, delete-orphan"
    )
    # OAuth tokens for email calendar integration
    oauth_tokens = relationship(
        "OAuthToken", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode(
            "utf-8"
        )

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    urgency = Column(Integer, default=5)  # 1-10
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(
        String(20), default="pending"
    )  # pending, in_progress, completed, archived
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    category = Column(String(50))
    tags = Column(JSON, default=list)
    reminder_sent = Column(Boolean, default=False)
    email_reminder = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    focus_time = Column(Integer, default=0)  # For tracking productivity

    user = relationship("User", back_populates="tasks")
    workflow_tasks = relationship(
        "WorkflowTask", back_populates="task", cascade="all, delete-orphan"
    )
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    shared_with = relationship("TaskShare", back_populates="task", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200), nullable=False)
    content = Column(Text)
    category = Column(String(50))
    tags = Column(JSON, default=list)
    is_pinned = Column(Boolean, default=False)
    color = Column(String(20), default="#ffffff")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="notes")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    all_day = Column(Boolean, default=False)
    location = Column(String(200))
    color = Column(String(20))
    reminder_minutes = Column(Integer, default=30)
    reminder_sent = Column(Boolean, default=False)
    recurrence = Column(String(50))  # none, daily, weekly, monthly
    recurrence_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # External calendar sync fields
    external_calendar_id = Column(
        String(500), nullable=True
    )  # ID from external calendar
    external_calendar_type = Column(String(50), nullable=True)  # google, outlook
    last_synced_at = Column(DateTime, nullable=True)  # Last sync time

    user = relationship("User", back_populates="calendar_events")


class OAuthToken(Base):
    """Store OAuth tokens for external calendar services"""

    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # google, outlook
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # When the token expires
    token_type = Column(String(50), default="Bearer")
    scope = Column(Text, nullable=True)  # OAuth scopes granted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optional: Store calendar ID for the user's primary calendar
    calendar_id = Column(String(200), nullable=True)  # For Google Calendar users

    user = relationship("User", back_populates="oauth_tokens")


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    trigger_type = Column(String(50))  # scheduled, event, manual, api
    trigger_config = Column(JSON)
    actions = Column(JSON)  # List of actions to perform
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workflows")
    tasks = relationship(
        "WorkflowTask", back_populates="workflow", cascade="all, delete-orphan"
    )


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"))
    order = Column(Integer)
    delay_minutes = Column(Integer, default=0)
    conditions = Column(JSON)

    workflow = relationship("Workflow", back_populates="tasks")
    task = relationship("Task", back_populates="workflow_tasks")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipient = Column(String(120))
    subject = Column(String(200))
    body = Column(Text)
    status = Column(String(20))  # sent, failed, pending
    sent_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="email_logs")


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    tasks_completed = Column(Integer, default=0)
    tasks_created = Column(Integer, default=0)
    notes_created = Column(Integer, default=0)
    events_attended = Column(Integer, default=0)
    productivity_score = Column(Float, default=0.0)
    daily_score = Column(Integer, default=0)  # 0 to 100 daily overall score
    focus_time_minutes = Column(Integer, default=0)
    best_focus_time = Column(String(50))  # e.g. "9AM - 11AM"
    metrics = Column(JSON, default=dict)

    user = relationship("User")

class TaskShare(Base):
    __tablename__ = "task_shares"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    shared_by_id = Column(Integer, ForeignKey("users.id"))
    shared_with_email = Column(String(120), nullable=False)
    permission = Column(String(20), default="view")  # view, edit
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="shared_with")
    shared_by = relationship("User", foreign_keys=[shared_by_id])

class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")
    user = relationship("User")

class UserContext(Base):
    """Memory Context for Smart AI Brain"""
    __tablename__ = "user_contexts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    habits = Column(JSON, default=list)  # E.g. [{"time": "10:00", "action": "check_emails"}]
    preferred_working_hours = Column(String(100))
    recent_interactions = Column(JSON, default=list)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
