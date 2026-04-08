import json
from app.database.db import get_db_connection

# TASK TOOLS
def create_task(title: str, description: str = "", urgency: str = "normal", user_id: int = 1) -> str:
    """Creates a new task in the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (user_id, title, description, urgency) VALUES (?, ?, ?, ?)",
            (user_id, title, description, urgency)
        )
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return json.dumps({"status": "success", "task_id": task_id, "message": f"Task '{title}' created successfully."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def get_all_tasks(user_id: int = 1) -> str:
    """Retrieves all tasks for the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return json.dumps({"tasks": tasks})

def complete_task(task_id: int) -> str:
    """Marks a task as completed."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return json.dumps({"status": "success", "message": f"Task {task_id} completed."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def delete_task(task_id: int) -> str:
    """Deletes a task by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return json.dumps({"status": "success", "message": f"Task {task_id} deleted."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# SCHEDULER TOOLS
def schedule_time(task_id: int, start_time: str, end_time: str, user_id: int = 1) -> str:
    """Assigns a time slot to a task. Time format: YYYY-MM-DD HH:MM"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO schedule (user_id, task_id, start_time, end_time) VALUES (?, ?, ?, ?)",
            (user_id, task_id, start_time, end_time)
        )
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return json.dumps({"status": "success", "schedule_id": schedule_id, "message": f"Scheduled task {task_id} from {start_time} to {end_time}."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def get_schedule(user_id: int = 1) -> str:
    """Retrieves the current schedule."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.start_time, s.end_time, t.title 
        FROM schedule s 
        JOIN tasks t ON s.task_id = t.id 
        WHERE s.user_id = ? 
        ORDER BY s.start_time
    ''', (user_id,))
    schedule = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return json.dumps({"schedule": schedule})

# NOTES TOOLS
def create_note(content: str, tags: str = "", user_id: int = 1) -> str:
    """Saves a new note."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notes (user_id, content, tags) VALUES (?, ?, ?)",
            (user_id, content, tags)
        )
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return json.dumps({"status": "success", "note_id": note_id, "message": "Note saved successfully."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def get_notes(user_id: int = 1) -> str:
    """Retrieves all notes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE user_id = ?", (user_id,))
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return json.dumps({"notes": notes})

# REMINDER TOOLS
def set_reminder(message: str, remind_at: str, user_id: int = 1) -> str:
    """Sets a reminder. format for remind_at: YYYY-MM-DD HH:MM"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, message, remind_at) VALUES (?, ?, ?)",
            (user_id, message, remind_at)
        )
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return json.dumps({"status": "success", "reminder_id": reminder_id, "message": f"Reminder set for {remind_at}."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def get_reminders(user_id: int = 1) -> str:
    """Retrieves pending reminders."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders WHERE user_id = ? ORDER BY remind_at", (user_id,))
    reminders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return json.dumps({"reminders": reminders})
