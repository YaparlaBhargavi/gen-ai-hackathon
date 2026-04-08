# app/agents/context_agent.py
from sqlalchemy.orm import Session
from app.database.models import UserContext
import json
from datetime import datetime

class ContextAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session

    def get_or_create_context(self) -> UserContext:
        context = self.db.query(UserContext).filter(UserContext.user_id == self.user_id).first()
        if not context:
            context = UserContext(user_id=self.user_id, habits=list(), recent_interactions=list())
            self.db.add(context)
            self.db.commit()
            self.db.refresh(context)
        return context

    def log_interaction(self, query: str, action_taken: str):
        """Log recent interactions to discover habits over time"""
        context = self.get_or_create_context()
        interactions = list(context.recent_interactions) if context.recent_interactions else []
        
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "action": action_taken
        }
        
        interactions.append(interaction)
        # Keep last 100 interactions
        if len(interactions) > 100:
            interactions = interactions[-100:]
            
        context.recent_interactions = interactions
        self.db.commit()
        
    def generate_suggestions(self) -> list:
        """Simple AI suggestion generation based on time of day"""
        hour = datetime.utcnow().hour
        # Convert to local time theoretically. We mock with UTC hour for now.
        suggestions = []
        if 8 <= hour <= 11:
            suggestions.append("You are usually highly productive in the morning! Focus on deep work.")
        elif 18 <= hour <= 22:
            suggestions.append("You typically delay tasks after 8PM. Consider wrapping up and relaxing.")
        return suggestions
