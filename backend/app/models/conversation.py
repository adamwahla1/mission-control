import enum
from uuid import UUID
from sqlalchemy import Column, String, Enum, ForeignKey, JSON, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


class MessageType(str, enum.Enum):
    DIRECT = "direct"
    BROADCAST = "broadcast"
    TASK_ASSIGNMENT = "task_assignment"
    RESPONSE = "response"
    ERROR = "error"


class Conversation(BaseModel):
    __tablename__ = "conversations"

    root_task_id = Column(PG_UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    message_count = Column(Integer, default=0)

    # Relationships
    messages = relationship("Message", back_populates="conversation")
    tasks = relationship("Task", back_populates="conversation")


class Message(BaseModel):
    __tablename__ = "messages"

    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    recipient_id = Column(PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    message_type = Column(Enum(MessageType), default=MessageType.DIRECT)
    payload = Column(JSON, nullable=False)
    parent_id = Column(PG_UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("Agent", foreign_keys=[sender_id])
    recipient = relationship("Agent", foreign_keys=[recipient_id])
    parent = relationship("Message", remote_side=["Message.id"], back_populates="replies")
    replies = relationship("Message", back_populates="parent")
