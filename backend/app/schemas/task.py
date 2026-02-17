from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List
from app.schemas.base import UUIDSchema

class TaskBase(BaseModel):
    title: str
    description: str | None = None
    priority: str = "medium"
    payload: Dict[str, Any] | None = None

class TaskCreate(TaskBase):
    pass

class TaskAssignRequest(BaseModel):
    agent_id: UUID

class TaskResponse(TaskBase, UUIDSchema):
    status: str
    result: Dict[str, Any] | None = None
    agent_id: UUID | None = None
    assigned_at: datetime | None = None
    completed_at: datetime | None = None
