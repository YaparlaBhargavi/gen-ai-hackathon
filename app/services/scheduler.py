# app/services/scheduler.py
import asyncio
from datetime import datetime, timedelta
from app.database.db import SessionLocal
from app.database.models import Workflow, Task, CalendarEvent

async def workflow_daemon():
    """Background Daemon to process Auto Workflow Engine"""
    while True:
        db = SessionLocal()
        try:
            # Get active scheduled workflows
            workflows = db.query(Workflow).filter(Workflow.is_active == True).all()
            for workflow in workflows:
                triggered = False
                action_message = ""
                
                # Check Conditions (Mock logic for IF/THEN)
                if workflow.trigger_type == "scheduled":
                    # IF scheduled time is met
                    if workflow.next_run and datetime.utcnow() >= workflow.next_run:
                        triggered = True
                        action_message = "Sent scheduled summary"
                        workflow.next_run = datetime.utcnow() + timedelta(days=1)
                
                elif workflow.trigger_type == "event":
                    # IF Task Overdue THEN Send notification
                    if "overdue" in workflow.description.lower():
                        overdue_tasks = db.query(Task).filter(Task.user_id == workflow.user_id, Task.status != 'completed', Task.due_date < datetime.utcnow()).all()
                        if overdue_tasks:
                            triggered = True
                            action_message = f"Sent notification for {len(overdue_tasks)} overdue tasks."
                            # In real app, call EmailAgent here to send to User
                    
                    # IF Meeting Tomorrow THEN Send Reminder
                    if "meeting tomorrow" in workflow.description.lower():
                        tomorrow = datetime.utcnow() + timedelta(days=1)
                        events = db.query(CalendarEvent).filter(CalendarEvent.user_id == workflow.user_id, CalendarEvent.start_time >= datetime.utcnow(), CalendarEvent.start_time <= tomorrow).all()
                        if events:
                            triggered = True
                            action_message = f"Sent reminders for {len(events)} upcoming meetings."
                
                if triggered:
                    print(f"[Workflow Engine] Executed workflow '{workflow.name}': {action_message}")
                    workflow.last_run = datetime.utcnow()
                    
            db.commit()
        except Exception as e:
            print(f"Workflow daemon error: {e}")
        finally:
            db.close()
            
        await asyncio.sleep(60) # check every minute

def start_scheduler():
    loop = asyncio.get_event_loop()
    loop.create_task(workflow_daemon())
