from sqlalchemy import Column, String, Boolean, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    full_name = Column(String(255))
    role = Column(String(50), default="viewer")  # super_admin, agent_manager, agent_operator, viewer, auditor
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Telegram integration
    telegram_chat_id = Column(BigInteger, nullable=True)
    agent_subscriptions = Column(JSONB, default=list)  # List of agent IDs to receive notifications for

    # Relationships
    created_tasks = relationship("Task", back_populates="created_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
