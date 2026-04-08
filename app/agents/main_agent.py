# app/agents/main_agent.py
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agents.task_agent import TaskAgent
from app.agents.calendar_agent import CalendarAgent
from app.agents.email_agent import EmailAgent
from app.agents.notes_agent import NotesAgent
from app.agents.analytics_agent import AnalyticsAgent
from app.agents.workflow_agent import WorkflowAgent

from app.agents.context_agent import ContextAgent
import re
from datetime import datetime, timedelta

class MainAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session
        self.task_agent = TaskAgent(user_id, db_session)
        self.calendar_agent = CalendarAgent(user_id, db_session)
        self.email_agent = EmailAgent(user_id, db_session)
        self.notes_agent = NotesAgent(user_id, db_session)
        self.analytics_agent = AnalyticsAgent(user_id, db_session)
        self.workflow_agent = WorkflowAgent(user_id, db_session)
        self.context_agent = ContextAgent(user_id, db_session)

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query using Smart AI Brain intent extraction"""
        query_lower = query.lower()
        
        # Log interaction for habit tracking
        self.context_agent.log_interaction(query, "Received query at Smart AI")
        
        # NLP Intent Extraction Regex Logic (Mock LLM)
        # E.g. "Finish ML project by Friday" -> Create Task
        if intent_data := self._extract_task_intent(query_lower, query):
            # Pass the structured text strictly for creating "finish project"
            import app.database.models as models
            task = models.Task(
                user_id=self.user_id, 
                title=intent_data['title'],
                due_date=intent_data['due_date'],
                urgency=8,
                priority="high"
            )
            self.db.add(task)
            self.db.commit()
            return {
                "status": "success",
                "response": f"🧠 AI Brain extracted intent:\nCreated task '{intent_data['title']}' due on {intent_data['due_date'].strftime('%A')}.\n\n💡 Suggestion: {self.context_agent.generate_suggestions()[0] if self.context_agent.generate_suggestions() else ''}"
            }

        # Task-related queries
        if any(
            keyword in query_lower
            for keyword in ["task", "todo", "to-do", "complete", "finish"]
        ):
            return await self.task_agent.process_task_query(query)

        # Calendar-related queries
        elif any(
            keyword in query_lower
            for keyword in ["calendar", "event", "meeting", "schedule", "appointment"]
        ):
            return await self.calendar_agent.process_calendar_query(query)

        # Email-related queries
        elif any(keyword in query_lower for keyword in ["email", "mail", "send"]):
            return await self.email_agent.process_email_query(query)

        # Notes-related queries
        elif any(
            keyword in query_lower for keyword in ["note", "memo", "remember", "idea"]
        ):
            return await self.notes_agent.process_notes_query(query)

        # Analytics queries
        elif any(
            keyword in query_lower
            for keyword in ["analytics", "stats", "report", "productivity", "insight"]
        ):
            return await self.analytics_agent.process_analytics_query(query)

        # Workflow queries
        elif any(
            keyword in query_lower
            for keyword in ["workflow", "automate", "auto", "trigger"]
        ):
            return await self.workflow_agent.process_workflow_query(query)

        # Help query
        elif any(
            keyword in query_lower
            for keyword in ["help", "what can you do", "commands"]
        ):
            return self.get_help_response()

        # Default response
        else:
            return {
                "status": "success",
                "response": "I can help you manage tasks, calendar events, emails, notes, and workflows. Type 'help' to see what I can do!",
            }
            
    def _extract_task_intent(self, q_lower: str, q_original: str):
        """Mock LLM structured action extractor"""
        match = re.search(r'(?:finish|complete) (.*?) by (monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today)', q_lower)
        if match:
            task_name = match.group(1).title()
            day_str = match.group(2)
            
            # calculate day offset
            today = datetime.utcnow()
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            if day_str == 'today':
                due_date = today
            elif day_str == 'tomorrow':
                due_date = today + timedelta(days=1)
            else:
                target_idx = days.index(day_str)
                current_idx = today.weekday()
                offset = (target_idx - current_idx) % 7
                if offset == 0: offset = 7
                due_date = today + timedelta(days=offset)
                
            return {
                "action": "create_task",
                "title": task_name,
                "due_date": due_date
            }
        return None

    def get_help_response(self) -> Dict[str, Any]:
        """Get help message"""
        help_text = "🤖 **Smart AI Brain - Help Guide**\n\n"
        help_text += "**Natural Language (Try it!):**\n"
        help_text += '• "Finish ML project by Friday"\n\n'
        help_text += "**Task Management:**\n"
        help_text += '• "Create a task to complete presentation"\n'
        help_text += '• "Show my pending tasks"\n'
        
        return {"status": "success", "response": help_text}

def run_main_agent(query: str, user_id: int, db_session):
    """Entry point for main agent"""
    import asyncio

    agent = MainAgent(user_id, db_session)
    return asyncio.run(agent.process_query(query))
