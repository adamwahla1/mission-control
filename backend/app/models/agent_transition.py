from uuid import UUID
from sqlalchemy import Column, String, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AgentStateTransition(BaseModel):
    __tablename__ = "agent_state_transitions"

    agent_id = Column(PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    from_status = Column(String(32), nullable=False)
    to_status = Column(String(32), nullable=False)
    reason = Column(String(500))
    transition_metadata = Column("metadata", JSON, default=dict)
    triggered_by = Column(String(255))

    agent = relationship("Agent", back_populates="state_transitions")
