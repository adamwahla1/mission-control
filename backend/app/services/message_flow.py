"""
Message Flow Service
Manages inter-agent messaging and conversation threading.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Message, Conversation, MessageType, ConversationStatus
from app.services.event_bus import event_bus


class MessageFlowService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(
        self,
        root_task_id: UUID = None,
        participant_ids: List[UUID] = None
    ) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            root_task_id=root_task_id,
            status=ConversationStatus.ACTIVE
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
    
    async def send_message(
        self,
        conversation_id: UUID,
        sender_id: UUID,
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.DIRECT,
        recipient_id: UUID = None,
        parent_id: UUID = None
    ) -> Message:
        """Send a message in a conversation"""
        # Verify conversation exists
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")
        
        # Create message
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            parent_id=parent_id
        )
        self.db.add(message)
        
        # Update conversation message count
        conversation.message_count += 1
        
        self.db.commit()
        self.db.refresh(message)
        
        # Broadcast message
        await event_bus.broadcast_conversation_message(
            conversation_id=conversation_id,
            message={
                'id': str(message.id),
                'sender_id': str(sender_id),
                'recipient_id': str(recipient_id) if recipient_id else None,
                'message_type': message_type.value,
                'payload': payload,
                'created_at': message.created_at.isoformat()
            }
        )
        
        return message
    
    def get_conversation_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """Get messages in a conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_message_thread(
        self,
        message_id: UUID
    ) -> List[Message]:
        """Get message and all its replies (recursive)"""
        # Get the root message
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return []
        
        # Build thread using recursive CTE (simplified)
        # In production, use SQLAlchemy's recursive CTE support
        messages = []
        current = message
        while current:
            messages.append(current)
            if current.parent_id:
                current = self.db.query(Message).filter(
                    Message.id == current.parent_id
                ).first()
            else:
                current = None
        
        return list(reversed(messages))
    
    def get_agent_conversations(
        self,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """Get conversations where agent participated"""
        return self.db.query(Conversation).join(
            Message, Message.conversation_id == Conversation.id
        ).filter(
            Message.sender_id == agent_id
        ).distinct().order_by(
            Conversation.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def close_conversation(self, conversation_id: UUID) -> Conversation:
        """Mark conversation as completed"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")
        
        conversation.status = ConversationStatus.COMPLETED
        self.db.commit()
        return conversation
    
    def get_conversation_stats(self) -> Dict[str, int]:
        """Get conversation counts by status"""
        stats = self.db.query(
            Conversation.status,
            func.count(Conversation.id)
        ).group_by(Conversation.status).all()
        
        return {status.value: count for status, count in stats}
