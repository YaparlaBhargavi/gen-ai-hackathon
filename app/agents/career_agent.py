# app/agents/career_agent.py
from typing import Dict, Any
from sqlalchemy.orm import Session


class CareerAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session

    async def process_career_query(self, query: str) -> Dict[str, Any]:
        """Process career-related queries"""
        query_lower = query.lower()

        if "skill" in query_lower or "learn" in query_lower:
            return await self.get_skill_advice()
        elif "goal" in query_lower or "career goal" in query_lower:
            return await self.set_career_goal(query)
        elif "productivity tips" in query_lower or "improve" in query_lower:
            return await self.get_productivity_tips()
        else:
            return await self.get_career_help()

    async def get_skill_advice(self) -> Dict[str, Any]:
        """Get skill development advice"""
        response = "📚 Skill Development Advice:\n\n"
        response += "Top in-demand skills for 2024-2025:\n"
        response += "1. 🤖 AI & Machine Learning\n"
        response += "2. 🐍 Python Programming\n"
        response += "3. ☁️ Cloud Computing (AWS, Azure)\n"
        response += "4. 📊 Data Science & Analytics\n"
        response += "5. 🔒 Cybersecurity\n"
        response += "6. 🚀 DevOps & CI/CD\n"
        response += "7. 📱 Full-Stack Development\n"
        response += "8. 🗄️ Database Management\n\n"
        response += "💡 Tip: Dedicate 30 minutes daily to learn a new skill!"

        return {"status": "success", "response": response}

    async def set_career_goal(self, query: str) -> Dict[str, Any]:
        """Set a career goal"""
        # Extract goal
        goal_match = query.replace("set", "").replace("career goal", "").strip()

        if not goal_match or len(goal_match) < 5:
            return {
                "status": "error",
                "response": "Please specify your career goal (e.g., 'Set career goal: Become a senior developer in 6 months')",
            }

        # Create a task for the goal
        from app.database.models import Task

        task = Task(
            user_id=self.user_id,
            title=f"🎯 CAREER GOAL: {goal_match}",
            urgency=8,
            status="pending",
            tags=["career", "goal"],
        )

        self.db.add(task)
        self.db.commit()

        response = f"🎯 Career goal set: '{goal_match}'\n\n"
        response += "💡 Tips to achieve your goal:\n"
        response += "• Break it down into smaller milestones\n"
        response += "• Dedicate time daily/weekly\n"
        response += "• Track your progress regularly\n"
        response += "• Celebrate small wins!\n\n"
        response += "I'll remind you to review your progress weekly!"

        return {"status": "success", "response": response}

    async def get_productivity_tips(self) -> Dict[str, Any]:
        """Get productivity tips"""
        tips = [
            "🎯 Use the Pomodoro Technique: 25 mins work, 5 mins break",
            "📋 Prioritize tasks using Eisenhower Matrix (Urgent/Important)",
            "🚫 Avoid multitasking - focus on one task at a time",
            "⏰ Time block your most important tasks for mornings",
            "📱 Turn off notifications during deep work sessions",
            "✅ Break large tasks into smaller, actionable steps",
            "🎉 Celebrate small wins to stay motivated",
            "💤 Get 7-8 hours of sleep for better focus",
        ]

        response = "💡 Productivity Tips:\n\n" + "\n".join(tips)

        return {"status": "success", "response": response}

    async def get_career_help(self) -> Dict[str, Any]:
        """Get career help"""
        return {
            "status": "success",
            "response": "💼 Career & Productivity Help:\n\n"
            "• What skills should I learn?\n"
            "• Set career goal: Become a team lead\n"
            "• Give me productivity tips\n"
            "• How to improve focus at work?",
        }
