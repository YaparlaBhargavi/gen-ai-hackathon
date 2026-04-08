# app/agents/workflow_agent.py
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Workflow
import re


class WorkflowAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session

    async def process_workflow_query(self, query: str) -> Dict[str, Any]:
        """Process workflow-related queries"""
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in ["create", "automate", "new"]):
            return await self.create_workflow(query)
        elif any(keyword in query_lower for keyword in ["list", "show", "view"]):
            return await self.list_workflows()
        elif any(keyword in query_lower for keyword in ["delete", "remove"]):
            return await self.delete_workflow(query)
        elif "activate" in query_lower or "enable" in query_lower:
            return await self.toggle_workflow(query, True)
        elif "deactivate" in query_lower or "disable" in query_lower:
            return await self.toggle_workflow(query, False)
        else:
            return await self.get_workflow_help()

    async def create_workflow(self, query: str) -> Dict[str, Any]:
        """Create a workflow from natural language"""
        # Extract workflow name
        name_match = re.search(
            r"(?:workflow|automation)[:\s]+(.+?)(?:to|that|$)", query, re.IGNORECASE
        )
        name = name_match.group(1).strip() if name_match else "New Workflow"

        # Determine trigger type
        trigger_type = "manual"
        if "daily" in query.lower():
            trigger_type = "scheduled"
        elif "weekly" in query.lower():
            trigger_type = "scheduled"

        workflow = Workflow(
            user_id=self.user_id,
            name=name[:100],
            description=query,
            trigger_type=trigger_type,
            is_active=True,
        )

        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)

        response_lines = [
            f"⚙️ Workflow created: '{name}'",
            "",
            "You can configure it in the Workflows page.",
        ]

        return {
            "status": "success",
            "response": "\n".join(response_lines),
            "workflow": {
                "id": workflow.id,
                "name": workflow.name,
                "trigger_type": workflow.trigger_type,
            },
        }

    async def list_workflows(self) -> Dict[str, Any]:
        """List all workflows"""
        workflows = (
            self.db.query(Workflow).filter(Workflow.user_id == self.user_id).all()
        )

        if not workflows:
            return {
                "status": "success",
                "response": "⚙️ No workflows yet. Create one to automate your tasks!\n\nExample: 'Create workflow to send daily task summary'",
            }

        workflow_list = []
        for i, w in enumerate(workflows, 1):
            status_icon = "🟢" if w.is_active else "🔴"
            trigger_icon = "⏰" if w.trigger_type == "scheduled" else "👆"
            workflow_list.append(f"{i}. {status_icon} {trigger_icon} {w.name}")

        response = "⚙️ Your Workflows:\n\n" + "\n".join(workflow_list)

        return {
            "status": "success",
            "response": response,
            "workflows": [
                {"id": w.id, "name": w.name, "active": w.is_active} for w in workflows
            ],
        }

    async def delete_workflow(self, query: str) -> Dict[str, Any]:
        """Delete a workflow"""
        workflow_id_match = re.search(r"(\d+)", query)
        if workflow_id_match:
            workflow_id = int(workflow_id_match.group(1))
            workflow = (
                self.db.query(Workflow)
                .filter(Workflow.id == workflow_id, Workflow.user_id == self.user_id)
                .first()
            )

            if workflow:
                name = workflow.name
                self.db.delete(workflow)
                self.db.commit()
                return {
                    "status": "success",
                    "response": f"🗑️ Workflow deleted: '{name}'",
                }

        return {
            "status": "error",
            "message": "Workflow not found. Please provide a valid workflow ID.",
        }

    async def toggle_workflow(self, query: str, activate: bool) -> Dict[str, Any]:
        """Activate or deactivate a workflow"""
        workflow_id_match = re.search(r"(\d+)", query)
        if workflow_id_match:
            workflow_id = int(workflow_id_match.group(1))
            workflow = (
                self.db.query(Workflow)
                .filter(Workflow.id == workflow_id, Workflow.user_id == self.user_id)
                .first()
            )

            if workflow:
                workflow.is_active = activate
                self.db.commit()
                action = "activated" if activate else "deactivated"
                return {
                    "status": "success",
                    "response": f"⚙️ Workflow '{workflow.name}' {action}",
                }

        return {"status": "error", "message": "Please provide a valid workflow ID"}

    async def get_workflow_help(self) -> Dict[str, Any]:
        """Get workflow help"""
        help_lines = [
            "⚙️ Workflow Automation Help:",
            "",
            "• Create workflow to send daily task summary",
            "• Create weekly report automation",
            "• Show my workflows",
            "• Delete workflow #1",
            "",
            "Workflows can automate repetitive tasks and send scheduled reports.",
        ]

        return {"status": "success", "response": "\n".join(help_lines)}
