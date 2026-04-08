# app/agents/collaboration_agent.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import Task, TaskShare, TaskComment, User

class CollaborationAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session

    def share_task(self, task_id: int, target_email: str, permission: str = "view") -> Dict[str, Any]:
        """Share a task with another user"""
        task = self.db.query(Task).filter(Task.id == task_id, Task.user_id == self.user_id).first()
        if not task:
            return {"status": "error", "message": "Task not found."}
            
        share = TaskShare(
            task_id=task_id,
            shared_by_id=self.user_id,
            shared_with_email=target_email,
            permission=permission
        )
        self.db.add(share)
        self.db.commit()
        
        return {"status": "success", "message": f"Task shared with {target_email}"}

    def add_comment(self, task_id: int, message: str) -> Dict[str, Any]:
        """Add a comment to a task"""
        # Validate task exists and user has access
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"status": "error", "message": "Task not found."}
            
        # Verify access: Is owner or is shared with user
        has_access = task.user_id == self.user_id
        if not has_access:
            user = self.db.query(User).filter(User.id == self.user_id).first()
            if user:
                share = self.db.query(TaskShare).filter(TaskShare.task_id == task_id, TaskShare.shared_with_email == user.email).first()
                if share:
                    has_access = True
                    
        if not has_access:
            return {"status": "error", "message": "Access denied."}
            
        comment = TaskComment(
            task_id=task_id,
            user_id=self.user_id,
            message=message
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        return {"status": "success", "message": "Comment added.", "comment_id": comment.id}

    def get_comments(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all comments for a task"""
        comments = self.db.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at.asc()).all()
        return [
            {
                "id": c.id,
                "user_id": c.user_id,
                "message": c.message,
                "created_at": c.created_at.isoformat()
            } for c in comments
        ]
