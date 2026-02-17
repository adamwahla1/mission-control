import enum
from sqlalchemy import Column, String, Integer, Enum, Boolean, DateTime
from app.models.base import BaseModel


class RetentionAction(str, enum.Enum):
    DELETE = "delete"
    ANONYMIZE = "anonymize"
    ARCHIVE = "archive"


class RetentionPolicy(BaseModel):
    __tablename__ = "retention_policies"

    policy_name = Column(String(128), unique=True, nullable=False)
    table_name = Column(String(128), nullable=False)
    retention_days = Column(Integer, nullable=False)
    action_after_retention = Column(Enum(RetentionAction), default=RetentionAction.DELETE)
    archive_table = Column(String(128))
    legal_hold_enabled = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    soft_delete_first = Column(Boolean, default=True)
    soft_delete_days = Column(Integer, default=7)
