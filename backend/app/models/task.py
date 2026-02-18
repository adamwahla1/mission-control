import enum
from uuid import UUID
from sqlalchemy import Column, String, Text, Enum, ForeignKey, JSON, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    __tablename__ = "tasks"

    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    payload = Column(JSON)
    result = Column(JSON)
    version = Column(Integer, default=1)
    assigned_at = Column(DateTime(timezone=True))
    claimed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    last_heartbeat = Column(DateTime(timezone=True))
    reclaim_count = Column(Integer, default=0)

    # Foreign Keys
    agent_id = Column(PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    created_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parent_task_id = Column(PG_UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)

    # Relationships
    assigned_agent = relationship("Agent", back_populates="assigned_tasks")
    created_by_user = relationship("User", back_populates="created_tasks")
    parent_task = relationship("Task", remote_side="Task.id", back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task")
    conversation = relationship("Conversation", back_populates="tasks")
