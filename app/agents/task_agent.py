# app/agents/task_agent.py
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models import Task
import re


class TaskAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session

    async def process_task_query(self, query: str) -> Dict[str, Any]:
        """Process task-related queries"""
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in ["create", "add", "new"]):
            return await self.create_task(query)
        elif any(keyword in query_lower for keyword in ["list", "show", "view", "all"]):
            return await self.list_tasks(query)
        elif any(keyword in query_lower for keyword in ["complete", "done", "finish"]):
            return await self.complete_task(query)
        elif any(keyword in query_lower for keyword in ["delete", "remove"]):
            return await self.delete_task(query)
        elif any(keyword in query_lower for keyword in ["update", "edit", "change"]):
            return await self.update_task(query)
        elif any(keyword in query_lower for keyword in ["search", "find"]):
            return await self.search_tasks(query)
        elif any(
            keyword in query_lower for keyword in ["urgent", "priority", "important"]
        ):
            return await self.get_urgent_tasks()
        else:
            return await self.get_task_insights()

    async def create_task(self, query: str) -> Dict[str, Any]:
        """Create task from natural language"""
        # Extract title
        title_match = re.search(
            r"(?:task|todo|to-do)[:\s]+(.+?)(?:by|due|priority|$)", query, re.IGNORECASE
        )
        if not title_match:
            title_match = re.search(
                r"create\s+(?:a\s+)?(?:task|todo)?\s*(.+?)(?:by|due|$)",
                query,
                re.IGNORECASE,
            )

        title = (
            title_match.group(1).strip()
            if title_match
            else query.replace("create", "")
            .replace("task", "")
            .replace("add", "")
            .strip()
        )

        if not title or len(title) < 3:
            return {"status": "error", "message": "Please provide a valid task title"}

        # Extract due date
        due_date = None
        today = datetime.now()

        if "today" in query.lower():
            due_date = today.replace(hour=23, minute=59, second=59)
        elif "tomorrow" in query.lower():
            due_date = (today + timedelta(days=1)).replace(
                hour=23, minute=59, second=59
            )
        elif "next week" in query.lower():
            due_date = (today + timedelta(days=7)).replace(
                hour=23, minute=59, second=59
            )
        elif "next month" in query.lower():
            due_date = (today + timedelta(days=30)).replace(
                hour=23, minute=59, second=59
            )
        else:
            # Try to extract specific date
            date_match = re.search(r"(\d{1,2})[/-](\d{1,2})", query)
            if date_match:
                try:
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    year = today.year
                    due_date = datetime(year, month, day, 23, 59, 59)
                    if due_date < today:
                        due_date = datetime(year + 1, month, day, 23, 59, 59)
                except ValueError:
                    pass

        # Extract urgency
        urgency = 5
        if any(
            word in query.lower()
            for word in ["critical", "urgent", "asap", "high priority"]
        ):
            urgency = 10
        elif "high" in query.lower():
            urgency = 8
        elif "medium" in query.lower():
            urgency = 5
        elif "low" in query.lower():
            urgency = 3

        # Extract description
        description = None
        desc_match = re.search(
            r"description[:\s]+(.+?)(?:$|by|due)", query, re.IGNORECASE
        )
        if desc_match:
            description = desc_match.group(1).strip()

        # Extract tags
        tags = []
        tag_match = re.search(r"#(\w+)", query)
        if tag_match:
            tags = [tag_match.group(1)]

        task = Task(
            user_id=self.user_id,
            title=title[:200],
            description=description,
            urgency=urgency,
            due_date=due_date,
            status="pending",
            tags=tags,
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        response = f"✅ Task created: '{title}'"
        if due_date:
            response += f"\n📅 Due: {due_date.strftime('%Y-%m-%d %I:%M %p')}"
        response += f"\n⚡ Urgency: {urgency}/10"

        return {
            "status": "success",
            "response": response,
            "task": {
                "id": task.id,
                "title": task.title,
                "urgency": task.urgency,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            },
        }

    async def list_tasks(self, query: str = "") -> Dict[str, Any]:
        """List tasks with filters"""
        query_lower = query.lower()

        # Build query
        task_query = self.db.query(Task).filter(Task.user_id == self.user_id)

        # Apply filters
        if "completed" in query_lower:
            task_query = task_query.filter(Task.status == "completed")
        elif "pending" in query_lower or "incomplete" in query_lower:
            task_query = task_query.filter(Task.status.in_(["pending", "in_progress"]))
        else:
            task_query = task_query.filter(Task.status.in_(["pending", "in_progress"]))

        if "urgent" in query_lower or "high priority" in query_lower:
            task_query = task_query.filter(Task.urgency >= 7)

        # Order by urgency and due date
        tasks = task_query.order_by(Task.urgency.desc(), Task.due_date).all()

        if not tasks:
            status_filter = "completed" if "completed" in query_lower else "pending"
            return {
                "status": "success",
                "response": f"📋 No {status_filter} tasks found! Great job! 🎉",
            }

        task_list = []
        for i, task in enumerate(tasks[:15], 1):
            urgency_emoji = (
                "🔴" if task.urgency >= 8 else "🟠" if task.urgency >= 5 else "🟢"
            )
            due_str = (
                f" (Due: {task.due_date.strftime('%b %d, %I:%M %p')})"
                if task.due_date
                else ""
            )
            status_icon = "✅" if task.status == "completed" else "⏳"
            task_list.append(
                f"{i}. {urgency_emoji} {status_icon} {task.title}{due_str} - {task.urgency}/10"
            )

        response = f"📋 Your Tasks ({len(tasks)} total):\n\n" + "\n".join(task_list)
        if len(tasks) > 15:
            response += f"\n\n... and {len(tasks) - 15} more tasks"

        return {
            "status": "success",
            "response": response,
            "tasks": [
                {"id": t.id, "title": t.title, "status": t.status} for t in tasks
            ],
        }

    async def complete_task(self, query: str) -> Dict[str, Any]:
        """Mark task as completed"""
        # Try to extract task ID
        task_id_match = re.search(r"(\d+)", query)
        if task_id_match:
            task_id = int(task_id_match.group(1))
            task = (
                self.db.query(Task)
                .filter(Task.id == task_id, Task.user_id == self.user_id)
                .first()
            )
        else:
            # Try to find by title
            title_match = re.search(
                r"(?:complete|done|finish)[:\s]+(.+?)(?:$)", query, re.IGNORECASE
            )
            if title_match:
                title = title_match.group(1).strip()
                task = (
                    self.db.query(Task)
                    .filter(
                        Task.title.ilike(f"%{title}%"),
                        Task.user_id == self.user_id,
                        Task.status.in_(["pending", "in_progress"]),
                    )
                    .first()
                )
            else:
                # Get the first pending task
                task = (
                    self.db.query(Task)
                    .filter(
                        Task.user_id == self.user_id,
                        Task.status.in_(["pending", "in_progress"]),
                    )
                    .first()
                )

                if not task:
                    return {
                        "status": "error",
                        "message": "No pending tasks to complete!",
                    }

        if task:
            task.status = "completed"
            task.completed_at = datetime.now()
            self.db.commit()

            return {
                "status": "success",
                "response": f"✅ Task completed: '{task.title}'! Great progress! 🎉",
            }

        return {
            "status": "error",
            "message": "Task not found. Please check the task ID or title.",
        }

    async def delete_task(self, query: str) -> Dict[str, Any]:
        """Delete a task"""
        task_id_match = re.search(r"(\d+)", query)
        if task_id_match:
            task_id = int(task_id_match.group(1))
            task = (
                self.db.query(Task)
                .filter(Task.id == task_id, Task.user_id == self.user_id)
                .first()
            )

            if task:
                title = task.title
                self.db.delete(task)
                self.db.commit()
                return {"status": "success", "response": f"🗑️ Task deleted: '{title}'"}

        return {
            "status": "error",
            "message": "Task not found. Please provide a valid task ID.",
        }

    async def update_task(self, query: str) -> Dict[str, Any]:
        """Update task details"""
        task_id_match = re.search(r"(\d+)", query)
        if not task_id_match:
            return {
                "status": "error",
                "message": "Please specify task ID (e.g., 'Update task #1 with urgency 9')",
            }

        task_id = int(task_id_match.group(1))
        task = (
            self.db.query(Task)
            .filter(Task.id == task_id, Task.user_id == self.user_id)
            .first()
        )

        if not task:
            return {"status": "error", "message": "Task not found"}

        updates = []

        # Update urgency
        urgency_match = re.search(r"urgency\s+(\d+)", query, re.IGNORECASE)
        if urgency_match:
            new_urgency = int(urgency_match.group(1))
            if 1 <= new_urgency <= 10:
                task.urgency = new_urgency
                updates.append(f"urgency to {new_urgency}/10")

        # Update title
        title_match = re.search(r"title[:\s]+(.+?)(?:$|by|with)", query, re.IGNORECASE)
        if title_match:
            task.title = title_match.group(1).strip()[:200]
            updates.append(f"title to '{task.title}'")

        # Update due date
        if "due" in query.lower():
            if "tomorrow" in query.lower():
                task.due_date = datetime.now() + timedelta(days=1)
                updates.append("due date to tomorrow")
            elif "next week" in query.lower():
                task.due_date = datetime.now() + timedelta(days=7)
                updates.append("due date to next week")

        self.db.commit()

        if updates:
            return {
                "status": "success",
                "response": f"✅ Task updated: Updated {', '.join(updates)}",
            }

        return {"status": "error", "message": "No valid updates specified"}

    async def search_tasks(self, query: str) -> Dict[str, Any]:
        """Search for tasks"""
        search_term = (
            query.replace("search", "").replace("find", "").replace("task", "").strip()
        )

        if not search_term:
            return {"status": "error", "message": "Please provide a search term"}

        tasks = (
            self.db.query(Task)
            .filter(
                Task.user_id == self.user_id,
                (
                    Task.title.ilike(f"%{search_term}%")
                    | Task.description.ilike(f"%{search_term}%")
                ),
            )
            .all()
        )

        if not tasks:
            return {
                "status": "success",
                "response": f"No tasks found matching '{search_term}'",
            }

        task_list = [f"• {t.title} (ID: {t.id})" for t in tasks[:10]]
        response = (
            f"Found {len(tasks)} task(s) matching '{search_term}':\n"
            + "\n".join(task_list)
        )

        return {
            "status": "success",
            "response": response,
            "tasks": [{"id": t.id, "title": t.title} for t in tasks],
        }

    async def get_urgent_tasks(self) -> Dict[str, Any]:
        """Get urgent/high priority tasks"""
        tasks = (
            self.db.query(Task)
            .filter(
                Task.user_id == self.user_id,
                Task.urgency >= 7,
                Task.status.in_(["pending", "in_progress"]),
            )
            .order_by(Task.urgency.desc(), Task.due_date)
            .all()
        )

        if not tasks:
            return {
                "status": "success",
                "response": "🎉 No urgent tasks! You're on top of everything!",
            }

        task_list = []
        for i, task in enumerate(tasks[:10], 1):
            due_str = (
                f" (Due: {task.due_date.strftime('%b %d')})" if task.due_date else ""
            )
            task_list.append(
                f"{i}. 🔴 {task.title}{due_str} - Urgency: {task.urgency}/10"
            )

        response = f"⚠️ Urgent Tasks ({len(tasks)}):\n\n" + "\n".join(task_list)

        return {
            "status": "success",
            "response": response,
            "urgent_tasks": [{"id": t.id, "title": t.title} for t in tasks],
        }

    async def get_task_insights(self) -> Dict[str, Any]:
        """Get task statistics and insights"""
        tasks = self.db.query(Task).filter(Task.user_id == self.user_id).all()

        total = len(tasks)
        completed = len([t for t in tasks if t.status == "completed"])
        pending = len([t for t in tasks if t.status in ["pending", "in_progress"]])
        high_priority = len(
            [t for t in tasks if t.urgency >= 7 and t.status != "completed"]
        )
        overdue = len(
            [
                t
                for t in tasks
                if t.due_date
                and t.due_date < datetime.now()
                and t.status != "completed"
            ]
        )

        completion_rate = (completed / total * 100) if total > 0 else 0

        response_lines = [
            "📊 Task Insights:",
            "",
            f"📋 Total Tasks: {total}",
            f"✅ Completed: {completed}",
            f"⏳ Pending: {pending}",
            f"⚠️ High Priority: {high_priority}",
            f"🔴 Overdue: {overdue}",
            f"📈 Completion Rate: {completion_rate:.1f}%",
        ]

        if overdue > 0:
            response_lines.append(
                f"\n⚠️ You have {overdue} overdue tasks! Focus on completing them soon."
            )
        elif high_priority > 0:
            response_lines.append(
                f"\n💪 You have {high_priority} high priority tasks. Stay focused!"
            )
        elif pending > 0:
            response_lines.append("\n🎯 You're making progress! Keep going!")
        else:
            response_lines.append(
                "\n🎉 Amazing! All tasks completed! Time for a break!"
            )

        response = "\n".join(response_lines)

        return {
            "status": "success",
            "response": response,
            "insights": {
                "total": total,
                "completed": completed,
                "pending": pending,
                "high_priority": high_priority,
                "overdue": overdue,
                "completion_rate": completion_rate,
            },
        }
