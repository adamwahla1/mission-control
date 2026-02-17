from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from app.websocket import sio

class EventBus:
    """Broadcast events to WebSocket rooms"""
    
    @staticmethod
    async def broadcast_agent_status_change(
        agent_id: UUID, 
        old_status: str, 
        new_status: str,
        metadata: Dict[str, Any] = None
    ):
        """Broadcast agent status change to relevant rooms"""
        event_data = {
            'event': 'agent:status_changed',
            'agent_id': str(agent_id),
            'old_status': old_status,
            'new_status': new_status,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        # Broadcast to agent-specific room
        await sio.emit('agent:status_changed', event_data, room=f'agent:{agent_id}')
        # Broadcast to dashboard (all connected clients)
        await sio.emit('agent:status_changed', event_data, room='dashboard')
    
    @staticmethod
    async def broadcast_agent_heartbeat(agent_id: UUID, metadata: Dict[str, Any]):
        """Broadcast agent heartbeat"""
        event_data = {
            'event': 'agent:heartbeat',
            'agent_id': str(agent_id),
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata
        }
        await sio.emit('agent:heartbeat', event_data, room=f'agent:{agent_id}')
    
    @staticmethod
    async def broadcast_task_created(task_id: UUID, task_data: Dict[str, Any]):
        """Broadcast new task creation"""
        event_data = {
            'event': 'task:created',
            'task_id': str(task_id),
            'task': task_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await sio.emit('task:created', event_data, room='dashboard')
    
    @staticmethod
    async def broadcast_task_assigned(task_id: UUID, agent_id: UUID, task_data: Dict[str, Any]):
        """Broadcast task assignment"""
        event_data = {
            'event': 'task:assigned',
            'task_id': str(task_id),
            'agent_id': str(agent_id),
            'task': task_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        # Notify task room
        await sio.emit('task:assigned', event_data, room=f'task:{task_id}')
        # Notify agent room
        await sio.emit('task:assigned', event_data, room=f'agent:{agent_id}')
        # Notify dashboard
        await sio.emit('task:assigned', event_data, room='dashboard')
    
    @staticmethod
    async def broadcast_task_updated(task_id: UUID, update_data: Dict[str, Any]):
        """Broadcast task progress update"""
        event_data = {
            'event': 'task:updated',
            'task_id': str(task_id),
            'update': update_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await sio.emit('task:updated', event_data, room=f'task:{task_id}')
        await sio.emit('task:updated', event_data, room='dashboard')
    
    @staticmethod
    async def broadcast_task_completed(task_id: UUID, result: Dict[str, Any]):
        """Broadcast task completion"""
        event_data = {
            'event': 'task:completed',
            'task_id': str(task_id),
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
        await sio.emit('task:completed', event_data, room=f'task:{task_id}')
        await sio.emit('task:completed', event_data, room='dashboard')
    
    @staticmethod
    async def broadcast_conversation_message(conversation_id: UUID, message: Dict[str, Any]):
        """Broadcast new conversation message"""
        event_data = {
            'event': 'conversation:message',
            'conversation_id': str(conversation_id),
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        await sio.emit('conversation:message', event_data, room=f'conversation:{conversation_id}')
    
    @staticmethod
    async def broadcast_system_alert(message: str, severity: str = 'info'):
        """Broadcast system-wide alert"""
        event_data = {
            'event': 'system:alert',
            'message': message,
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat()
        }
        await sio.emit('system:alert', event_data, room='dashboard')

event_bus = EventBus()
