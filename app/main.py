# app/main.py

import os
import secrets
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import asyncio

import httpx
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    Depends,
    BackgroundTasks,
    HTTPException,
    Form,
    Request,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

# Local imports - ALL at the top
from app.auth.auth import create_access_token, get_current_user_optional
from app.database.db import engine, get_db, SessionLocal
from app.database.models import Base, User, CalendarEvent, Task, Note, Workflow
from app.services.email_calendar_sync import EmailCalendarSync

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Advitiyans Bot", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

templates = Jinja2Templates(directory=str(static_path.parent / "templates"))


# Pydantic schemas
class TaskSchema(BaseModel):
    title: str
    urgency: int
    due_date: Optional[str] = None
    task_status: Optional[str] = "pending"


class WorkflowSchema(BaseModel):
    name: str
    description: str
    trigger_type: str
    actions: list


class CalendarEventSchema(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: str
    end_time: str
    location: Optional[str] = None


# Routes
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    html_path = static_path.parent / "templates" / "index.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h1>Advitiyans Bot</h1><p>Welcome to Advitiyans Bot</p>",
        status_code=200,
    )


@app.get("/signup", response_class=HTMLResponse)
async def serve_signup(request: Request):
    html = templates.get_template("signup.html").render({"request": request})
    return HTMLResponse(html)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app": "Advitiyans Bot",
    }


@app.get("/calendar", response_class=HTMLResponse)
async def serve_calendar(request: Request, db: Session = Depends(get_db)):
    """Serve calendar page with user authentication"""
    user = await get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "calendar.html", {"request": request, "user": user}
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": user}
    )


@app.get("/tasks", response_class=HTMLResponse)
async def serve_tasks(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    return templates.TemplateResponse("tasks.html", {"request": request, "user": user})


@app.get("/workflows", response_class=HTMLResponse)
async def serve_workflows(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    return templates.TemplateResponse(
        "workflows.html", {"request": request, "user": user}
    )


@app.get("/analytics", response_class=HTMLResponse)
async def serve_analytics(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    return templates.TemplateResponse(
        "analytics.html", {"request": request, "user": user}
    )


@app.get("/notes", response_class=HTMLResponse)
async def serve_notes(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    return templates.TemplateResponse("notes.html", {"request": request, "user": user})


@app.get("/login", response_class=HTMLResponse)
async def serve_login(request: Request):
    html = templates.get_template("login.html").render({"request": request})
    return HTMLResponse(html)


@app.post("/signup", response_class=HTMLResponse)
async def process_signup(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    if password != confirm_password:
        html = templates.get_template("signup.html").render(
            {"request": request, "error": "Passwords do not match"}
        )
        return HTMLResponse(html)

    existing = (
        db.query(User)
        .filter(or_(User.username == username, User.email == email))
        .first()
    )

    if existing:
        html = templates.get_template("signup.html").render(
            {"request": request, "error": "Username or email already exists"}
        )
        return HTMLResponse(html)

    user = User(full_name=full_name, username=username, email=email)
    user.set_password(password)
    db.add(user)
    db.commit()

    token = create_access_token({"sub": user.username})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=False, max_age=86400)
    return response


@app.post("/login", response_class=HTMLResponse)
async def process_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(or_(User.username == username, User.email == username))
        .first()
    )

    if not user or not user.check_password(password):
        html = templates.get_template("login.html").render(
            {"request": request, "error": "Invalid username or password"}
        )
        return HTMLResponse(html)

    token = create_access_token({"sub": user.username})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=False, max_age=86400)
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response


@app.get("/api/auth/google/login")
async def google_login():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        return HTMLResponse(
            "Google Auth not configured: missing GOOGLE_CLIENT_ID in .env",
            status_code=500,
        )

    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/google/callback"
    )
    scope = "openid email profile https://www.googleapis.com/auth/calendar"
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return RedirectResponse(url)


@app.get("/api/auth/google/callback")
async def google_callback(request: Request, code: str, db: Session = Depends(get_db)):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/google/callback"
    )

    if not client_id or not client_secret:
        return HTMLResponse("Missing Google OAuth credentials in .env", status_code=500)

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            logger.error(f"Google token exchange failed: {response.text}")
            return HTMLResponse(
                f"Failed to authenticate with Google: {response.text}", status_code=400
            )

        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_info_resp = await client.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_info_resp.status_code != 200:
            logger.error(f"Failed to fetch user info: {user_info_resp.text}")
            return HTMLResponse(
                "Failed to fetch user profile from Google", status_code=400
            )

        user_info = user_info_resp.json()
        email = user_info.get("email")
        name = user_info.get("name")
        sub = user_info.get("sub")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            username = f"{email.split('@')[0]}_{sub[-4:]}"
            user = User(email=email, full_name=name, username=username)
            user.set_password(secrets.token_urlsafe(16))
            db.add(user)
            db.commit()

        # Store Google tokens for the user
        user.google_access_token = access_token
        user.google_refresh_token = refresh_token
        db.commit()

        token = create_access_token({"sub": user.username})
        redirect = RedirectResponse(url="/dashboard", status_code=302)
        redirect.set_cookie(
            key="access_token", value=token, httponly=False, max_age=86400
        )
        return redirect


@app.get("/profile", response_class=HTMLResponse)
async def serve_profile(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    return templates.TemplateResponse(
        "profile.html", {"request": request, "user": user}
    )


@app.get("/admin", response_class=HTMLResponse)
async def serve_admin(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    return templates.TemplateResponse("admin.html", {"request": request, "user": user})


# ============ CALENDAR API ENDPOINTS ============


@app.get("/api/calendar/events")
async def get_calendar_events(
    request: Request,
    start: Optional[str] = Query(None, description="Start date in ISO format"),
    end: Optional[str] = Query(None, description="End date in ISO format"),
    db: Session = Depends(get_db),
):
    """Get calendar events for the current user"""
    try:
        user = await get_current_user_optional(request, db)
        if not user:
            logger.warning("Unauthorized access to calendar events")
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Unauthorized. Please login.",
                    "events": [],
                },
            )

        logger.info(f"Fetching calendar events for user: {user.id}")

        query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user.id)

        if start:
            try:
                start_date = datetime.fromisoformat(start.replace("Z", "+00:00"))
                query = query.filter(CalendarEvent.start_time >= start_date)
            except ValueError as e:
                logger.warning(f"Invalid start date format: {e}")

        if end:
            try:
                end_date = datetime.fromisoformat(end.replace("Z", "+00:00"))
                query = query.filter(CalendarEvent.end_time <= end_date)
            except ValueError as e:
                logger.warning(f"Invalid end date format: {e}")
        else:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            next_month = today + timedelta(days=30)
            query = query.filter(
                and_(
                    CalendarEvent.start_time >= today,
                    CalendarEvent.start_time <= next_month,
                )
            )

        events = query.order_by(CalendarEvent.start_time).all()

        return {
            "success": True,
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "description": e.description or "",
                    "start": e.start_time.isoformat(),
                    "end": e.end_time.isoformat(),
                    "location": e.location or "",
                    "status": e.status or "pending",
                }
                for e in events
            ],
        }
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e), "events": []}
        )


@app.post("/api/calendar/events")
async def create_calendar_event(
    request: Request, event: CalendarEventSchema, db: Session = Depends(get_db)
):
    """Create a new calendar event"""
    try:
        user = await get_current_user_optional(request, db)
        if not user:
            logger.warning("Unauthorized attempt to create calendar event")
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Unauthorized. Please login."},
            )

        logger.info(f"Creating calendar event for user: {user.id}")

        start_time = datetime.fromisoformat(event.start_time.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(event.end_time.replace("Z", "+00:00"))

        db_event = CalendarEvent(
            user_id=user.id,
            title=event.title,
            description=event.description,
            start_time=start_time,
            end_time=end_time,
            location=event.location,
            status="pending",
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)

        logger.info(f"Calendar event created: {db_event.id} for user {user.id}")

        return {
            "success": True,
            "event": {
                "id": db_event.id,
                "title": db_event.title,
                "description": db_event.description or "",
                "start": db_event.start_time.isoformat(),
                "end": db_event.end_time.isoformat(),
                "location": db_event.location or "",
                "status": db_event.status,
            },
        }
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.put("/api/calendar/events/{event_id}")
async def update_calendar_event(
    event_id: int,
    request: Request,
    event: CalendarEventSchema,
    db: Session = Depends(get_db),
):
    """Update a calendar event"""
    try:
        user = await get_current_user_optional(request, db)
        if not user:
            return JSONResponse(
                status_code=401, content={"success": False, "error": "Unauthorized"}
            )

        db_event = (
            db.query(CalendarEvent)
            .filter(CalendarEvent.id == event_id, CalendarEvent.user_id == user.id)
            .first()
        )

        if not db_event:
            return JSONResponse(
                status_code=404, content={"success": False, "error": "Event not found"}
            )

        db_event.title = event.title
        db_event.description = event.description
        db_event.start_time = datetime.fromisoformat(
            event.start_time.replace("Z", "+00:00")
        )
        db_event.end_time = datetime.fromisoformat(
            event.end_time.replace("Z", "+00:00")
        )
        db_event.location = event.location

        db.commit()
        db.refresh(db_event)

        logger.info(f"Calendar event updated: {event_id} for user {user.id}")

        return {
            "success": True,
            "event": {
                "id": db_event.id,
                "title": db_event.title,
                "description": db_event.description or "",
                "start": db_event.start_time.isoformat(),
                "end": db_event.end_time.isoformat(),
                "location": db_event.location or "",
                "status": db_event.status,
            },
        }
    except Exception as e:
        logger.error(f"Error updating calendar event: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.delete("/api/calendar/events/{event_id}")
async def delete_calendar_event(
    event_id: int, request: Request, db: Session = Depends(get_db)
):
    """Delete a calendar event"""
    try:
        user = await get_current_user_optional(request, db)
        if not user:
            logger.warning("Unauthorized attempt to delete calendar event")
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Unauthorized. Please login."},
            )

        db_event = (
            db.query(CalendarEvent)
            .filter(CalendarEvent.id == event_id, CalendarEvent.user_id == user.id)
            .first()
        )

        if not db_event:
            return JSONResponse(
                status_code=404, content={"success": False, "error": "Event not found"}
            )

        db.delete(db_event)
        db.commit()

        logger.info(f"Calendar event deleted: {event_id} for user {user.id}")

        return {"success": True, "message": "Event deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.post("/api/calendar/events/{event_id}/sync")
async def sync_calendar_event(
    event_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Sync a calendar event to Google Calendar"""
    try:
        user = await get_current_user_optional(request, db)
        if not user:
            logger.warning("Unauthorized attempt to sync calendar event")
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Unauthorized. Please login."},
            )

        event = (
            db.query(CalendarEvent)
            .filter(CalendarEvent.id == event_id, CalendarEvent.user_id == user.id)
            .first()
        )

        if not event:
            return JSONResponse(
                status_code=404, content={"success": False, "error": "Event not found"}
            )

        if not user.google_access_token:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Google Calendar not connected. Please login with Google first.",
                },
            )

        sync_service = EmailCalendarSync(db)
        background_tasks.add_task(sync_service.sync_to_google_calendar, user.id, event)

        return {"success": True, "message": f"Sync started for event: {event.title}"}
    except Exception as e:
        logger.error(f"Error syncing calendar event: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/api/calendar/events/{event_id}")
async def get_event(event_id: int, request: Request, db: Session = Depends(get_db)):
    """Get a single calendar event"""
    try:
        user = await get_current_user_optional(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        event = (
            db.query(CalendarEvent)
            .filter(CalendarEvent.id == event_id, CalendarEvent.user_id == user.id)
            .first()
        )

        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        return {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "location": event.location,
            "status": event.status,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============ OTHER API ENDPOINTS ============


@app.get("/api/analytics/metrics")
async def get_analytics_metrics(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    user_id = user.id if user else 1

    from app.agents.analytics_agent import AnalyticsAgent

    agent = AnalyticsAgent(user_id, db)
    report = await agent.get_productivity_report()
    data = report["analytics"]

    return {
        "productivity_score": data["score"],
        "tasks_completed": data["completed_tasks"],
        "tasks_pending": data["total_tasks"] - data["completed_tasks"],
        "tasks_total": data["total_tasks"],
        "notes_total": data["total_notes"],
        "focus_time": data.get("focus_time", 0),
        "suggestion": (
            "You are most productive at 9AM"
            if data["score"] > 0
            else "Start a task to get AI insights!"
        ),
    }


@app.get("/api/stats")
async def get_stats(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    user_id = user.id if user else 1

    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    notes = (
        db.query(Note)
        .filter(Note.user_id == user_id)
        .order_by(Note.created_at.desc())
        .limit(5)
        .all()
    )

    completed = [t for t in tasks if t.status == "completed"]
    pending = [t for t in tasks if t.status != "completed"]
    high_priority = [t for t in pending if (t.urgency or 0) >= 8]

    recent_tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id, Task.status != "completed")
        .order_by(Task.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_tasks": len(tasks),
        "completed_tasks": len(completed),
        "high_priority_tasks": len(high_priority),
        "completion_rate": (len(completed) / len(tasks) * 100) if tasks else 0,
        "recent_tasks": [
            {"id": t.id, "title": t.title, "urgency": t.urgency} for t in recent_tasks
        ],
        "recent_notes": [
            {"id": n.id, "title": n.title, "content": n.content} for n in notes
        ],
    }


@app.post("/api/query")
async def process_ai_query(query: str, user_id: int = 1, db: Session = Depends(get_db)):
    from app.agents.main_agent import MainAgent

    agent = MainAgent(user_id, db)
    return await agent.process_query(query)


@app.get("/api/tasks")
async def get_tasks(user_id: int = 1, limit: int = 100, db: Session = Depends(get_db)):
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": t.id,
            "title": t.title,
            "urgency": t.urgency,
            "due_date": t.due_date,
            "task_status": t.status,
        }
        for t in tasks
    ]


@app.post("/api/tasks")
async def create_task(
    data: TaskSchema, user_id: int = 1, db: Session = Depends(get_db)
):
    due = datetime.fromisoformat(data.due_date) if data.due_date else None
    task = Task(
        user_id=user_id,
        title=data.title,
        urgency=data.urgency,
        due_date=due,
        status=data.task_status,
    )
    db.add(task)
    db.commit()
    return {"status": "success", "id": task.id}


@app.put("/api/tasks/{task_id}")
async def update_task(
    task_id: int, data: dict, user_id: int = 1, db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404)

    if "task_status" in data:
        task.status = data["task_status"]

    db.commit()
    return {"status": "success"}


@app.delete("/api/tasks/{task_id}")
async def delete_task_route(
    task_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if task:
        db.delete(task)
        db.commit()

    return {"status": "success"}


@app.get("/api/workflows")
async def get_workflows(user_id: int = 1, db: Session = Depends(get_db)):
    workflows = db.query(Workflow).filter(Workflow.user_id == user_id).all()

    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "trigger_type": w.trigger_type,
            "is_active": w.is_active,
        }
        for w in workflows
    ]


@app.post("/api/workflows")
async def create_workflow(
    data: WorkflowSchema, user_id: int = 1, db: Session = Depends(get_db)
):
    workflow = Workflow(
        user_id=user_id,
        name=data.name,
        description=data.description,
        trigger_type=data.trigger_type,
        actions=data.actions,
        is_active=True,
    )
    db.add(workflow)
    db.commit()
    return {"status": "success", "id": workflow.id}


@app.post("/api/workflows/{wf_id}/toggle")
async def toggle_workflow(wf_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    workflow = (
        db.query(Workflow)
        .filter(Workflow.id == wf_id, Workflow.user_id == user_id)
        .first()
    )

    if not workflow:
        raise HTTPException(status_code=404)

    workflow.is_active = not workflow.is_active
    db.commit()
    return {"status": "success", "is_active": workflow.is_active}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Advitiyans Bot...")

    from app.services.scheduler import workflow_daemon

    asyncio.create_task(workflow_daemon())

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                full_name="Administrator",
            )
            admin.set_password("admin123")
            db.add(admin)
            db.commit()
            logger.info("Admin user created")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
    finally:
        db.close()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Advitiyans Bot...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
