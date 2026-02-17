from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any
from app.schemas.base import UUIDSchema

class AgentBase(BaseModel):
    name: str
    agent_type: str = "subagent"
    capabilities: List[str] = []
    config: Dict[str, Any] = {}

class AgentCreate(AgentBase):
    parent_id: UUID | None = None

class AgentUpdate(BaseModel):
    name: str | None = None
    capabilities: List[str] | None = None
    config: Dict[str, Any] | None = None

class AgentResponse(AgentBase, UUIDSchema):
    status: str
    previous_status: str | None = None
    metadata: Dict[str, Any] = {}
    last_heartbeat: datetime | None = None

class AgentControlRequest(BaseModel):
    action: str  # pause, resume, restart, stop
