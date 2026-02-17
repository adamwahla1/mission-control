from sqlalchemy import Column, BigInteger, String, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True)
    event_id = Column(UUID(as_uuid=True), unique=True)
    event_type = Column(String(64), nullable=False)
    actor_type = Column(String(32), nullable=False)
    actor_id = Column(String(255))
    target_type = Column(String(64), nullable=False)
    target_id = Column(String(255))
    action = Column(String(16), nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="audit_logs")
