from uuid import UUID
import enum
from sqlalchemy import Column, String, Enum, JSON, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    OFFLINE = "offline"


class AgentType(str, enum.Enum):
    MAIN = "main"
    SUBAGENT = "subagent"
    WORKER = "worker"


class Agent(BaseModel):
    __tablename__ = "agents"

    name = Column(String(255), nullable=False)
    agent_type = Column(Enum(AgentType), default=AgentType.SUBAGENT)
    status = Column(Enum(AgentStatus), default=AgentStatus.IDLE)
    previous_status = Column(Enum(AgentStatus), nullable=True)
    capabilities = Column(JSON, default=list)
    config = Column(JSON, default=dict)
    agent_metadata = Column("metadata", JSON, default=dict)
    version = Column(Integer, default=1)
    last_heartbeat = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

    # Relationships
    parent_id = Column(PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    parent = relationship("Agent", remote_side=["Agent.id"], back_populates="children")
    children = relationship("Agent", back_populates="parent")
    assigned_tasks = relationship("Task", back_populates="assigned_agent")
    state_transitions = relationship("AgentStateTransition", back_populates="agent")
