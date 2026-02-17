import enum
from sqlalchemy import Column, String, Text, Integer, JSON, Enum, DateTime
from app.models.base import BaseModel


class FailureReason(str, enum.Enum):
    TIMEOUT = "timeout"
    ERROR = "error"
    CIRCUIT_OPEN = "circuit_open"
    REJECTED = "rejected"


class DeadLetterQueue(BaseModel):
    __tablename__ = "dead_letter_queue"

    original_task = Column(JSON, nullable=False)
    error = Column(Text, nullable=False)
    stack_trace = Column(Text)
    failure_reason = Column(Enum(FailureReason), nullable=False)
    retry_count = Column(Integer, default=0)
    reprocessed_at = Column(DateTime(timezone=True))
