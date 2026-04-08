'''app/models/workflow.py - Pydantic workflow models'''
from pydantic import BaseModel
from typing import List, Optional

class WorkflowStep(BaseModel):
    title: str
    priority: int
    description: Optional[str] = None

class WorkflowCreate(BaseModel):
    name: str
    steps: List[WorkflowStep]

class WorkflowResponse(BaseModel):
    id: int
    name: str
    steps: List[WorkflowStep]
    status: str = 'draft'

