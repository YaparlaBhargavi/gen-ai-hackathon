# app/agents/analytics_agent.py
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models import Task, Note, CalendarEvent


class AnalyticsAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session

    async def process_analytics_query(self, query: str) -> Dict[str, Any]:
        """Process analytics-related queries"""
        query_lower = query.lower()

        if (
            "productivity" in query_lower
            or "stats" in query_lower
            or "report" in query_lower
        ):
            return await self.get_productivity_report()
        elif "weekly" in query_lower or "this week" in query_lower:
            return await self.get_weekly_report()
        elif "monthly" in query_lower or "this month" in query_lower:
            return await self.get_monthly_report()
        elif "trends" in query_lower or "insights" in query_lower:
            return await self.get_insights()
        else:
            return await self.get_dashboard_stats()

    async def get_productivity_report(self) -> Dict[str, Any]:
        """Get comprehensive productivity report with 0-100 Score"""
        tasks = self.db.query(Task).filter(Task.user_id == self.user_id).all()
        notes = self.db.query(Note).filter(Note.user_id == self.user_id).all()
        events = (
            self.db.query(CalendarEvent)
            .filter(CalendarEvent.user_id == self.user_id)
            .all()
        )

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == "completed"])
        pending_tasks = len(
            [t for t in tasks if t.status in ["pending", "in_progress"]]
        )
        high_priority = len(
            [t for t in tasks if t.urgency >= 7 and t.status != "completed"]
        )
        overdue_tasks = len(
            [
                t for t in tasks
                if t.due_date and t.due_date < datetime.now() and t.status != "completed"
            ]
        )

        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate AI Productivity Score (0-100)
        focus_time = sum([t.focus_time for t in tasks if t.focus_time])
        base_score = completion_rate * 0.7
        focus_bonus = min(30, (focus_time / 120) * 30) # 2 hours focus = max 30 pts
        penalty = min(20, overdue_tasks * 5)
        productivity_score = max(0, min(100, base_score + focus_bonus - penalty))

        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_tasks = len([t for t in tasks if t.created_at >= week_ago])
        recent_completions = len(
            [t for t in tasks if t.completed_at and t.completed_at >= week_ago]
        )

        response = "📊 Productivity Report\n" + "=" * 30 + "\n\n"
        response += f"🌟 Daily AI Score: {int(productivity_score)}/100\n\n"
        response += "📋 Tasks Overview:\n"
        response += f"   • Total: {total_tasks}\n"
        response += f"   • Completed: {completed_tasks} ({completion_rate:.1f}%)\n"
        response += f"   • Overdue: {overdue_tasks}\n\n"
        response += f"⏱️ Focus Time: {int(focus_time)} minutes\n\n"

        # Insights
        if productivity_score >= 80:
            response += "\n🎉 You are currently a Productivity Master! Keep it up."
        elif productivity_score >= 50:
            response += "\n👍 Good progress today."
        

        return {
            "status": "success",
            "response": response,
            "analytics": {
                "score": int(productivity_score),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": completion_rate,
                "overdue": overdue_tasks,
                "total_notes": len(notes),
                "total_events": len(events),
                "focus_time": focus_time
            },
        }

    async def get_weekly_report(self) -> Dict[str, Any]:
        """Get weekly report"""
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_end = week_start + timedelta(days=7)

        tasks = (
            self.db.query(Task)
            .filter(Task.user_id == self.user_id, Task.created_at >= week_start)
            .all()
        )

        completed = len([t for t in tasks if t.status == "completed"])

        response = (
            "📊 Weekly Report ("
            + week_start.strftime("%b %d")
            + " - "
            + week_end.strftime("%b %d")
            + ")\n"
            + "=" * 40
            + "\n\n"
        )
        response += f"✅ Tasks Completed: {completed}\n"
        response += f"📋 Tasks Created: {len(tasks)}\n"

        if len(tasks) > 0:
            completion_rate = completed / len(tasks) * 100
            response += f"📈 Completion Rate: {completion_rate:.1f}%\n"

        return {"status": "success", "response": response}

    async def get_monthly_report(self) -> Dict[str, Any]:
        """Get monthly report"""
        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        tasks = (
            self.db.query(Task)
            .filter(Task.user_id == self.user_id, Task.created_at >= month_start)
            .all()
        )

        completed = len([t for t in tasks if t.status == "completed"])

        response = (
            "📊 Monthly Report ("
            + month_start.strftime("%B %Y")
            + ")\n"
            + "=" * 40
            + "\n\n"
        )
        response += f"✅ Tasks Completed: {completed}\n"
        response += f"📋 Tasks Created: {len(tasks)}\n"

        if len(tasks) > 0:
            completion_rate = completed / len(tasks) * 100
            response += f"📈 Completion Rate: {completion_rate:.1f}%\n"

        return {"status": "success", "response": response}

    async def get_insights(self) -> Dict[str, Any]:
        """Get AI-powered insights"""
        tasks = self.db.query(Task).filter(Task.user_id == self.user_id).all()

        if not tasks:
            return {
                "status": "success",
                "response": "Create some tasks to get personalized insights!",
            }

        completed = len([t for t in tasks if t.status == "completed"])
        pending = len([t for t in tasks if t.status in ["pending", "in_progress"]])
        high_priority_pending = len(
            [t for t in tasks if t.urgency >= 7 and t.status != "completed"]
        )

        insights = []

        if high_priority_pending > 3:
            insights.append(
                f"⚠️ You have {high_priority_pending} high priority pending tasks. Consider focusing on these first."
            )
        elif high_priority_pending > 0:
            insights.append(
                f"💪 Focus on completing your {high_priority_pending} high priority tasks."
            )

        if pending > 10:
            insights.append(
                f"📋 You have {pending} pending tasks. Break them down into smaller chunks."
            )

        if completed > 0 and pending > 0:
            ratio = completed / (completed + pending)
            if ratio < 0.3:
                insights.append("🎯 Try to complete more tasks before adding new ones.")
            elif ratio > 0.7:
                insights.append("🌟 Amazing productivity! Keep up the great work!")

        response = (
            "💡 AI Insights:\n\n" + "\n".join(insights)
            if insights
            else "Keep using the app to get personalized insights!"
        )

        return {"status": "success", "response": response, "insights": insights}

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get quick dashboard stats"""
        tasks = self.db.query(Task).filter(Task.user_id == self.user_id).all()
        notes = self.db.query(Note).filter(Note.user_id == self.user_id).all()

        total_tasks = len(tasks)
        completed = len([t for t in tasks if t.status == "completed"])
        pending = len([t for t in tasks if t.status in ["pending", "in_progress"]])
        high_priority = len(
            [t for t in tasks if t.urgency >= 7 and t.status != "completed"]
        )

        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0

        response = "📊 Quick Stats:\n\n"
        response += f"📋 Tasks: {total_tasks} total\n"
        response += f"   ✅ Completed: {completed}\n"
        response += f"   ⏳ Pending: {pending}\n"
        response += f"   ⚠️ High Priority: {high_priority}\n"
        response += f"   📈 Completion Rate: {completion_rate:.1f}%\n\n"
        response += f"📝 Notes: {len(notes)} total"

        return {"status": "success", "response": response}
