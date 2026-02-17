from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List
from app.schemas.base import UUIDSchema

class MessageBase(BaseModel):
    conversation_id: UUID
    sender_id: UUID
    recipient_id: UUID | None = None
    message_type: str = "direct"
    payload: Dict[str, Any]

class MessageResponse(MessageBase, UUIDSchema):
    pass

class ConversationResponse(UUIDSchema):
    root_task_id: UUID | None = None
    status: str
    message_count: int = 0
