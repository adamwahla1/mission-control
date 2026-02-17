import socketio
from fastapi import FastAPI
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.config import settings
from app.database import SessionLocal
from app.models import User

# Create Socket.io server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,
    ping_timeout=30,
    ping_interval=25,
    max_http_buffer_size=1_000_000  # 1MB
)

# Create ASGI app
socket_app = socketio.ASGIApp(sio)

async def get_user_from_token(token: str) -> User | None:
    """Validate JWT and return user"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
        finally:
            db.close()
    except JWTError:
        return None

# Connection handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle new WebSocket connection"""
    token = auth.get('token') if auth else None
    
    if not token:
        raise ConnectionRefusedError('Authentication required')
    
    user = await get_user_from_token(token)
    if not user or not user.is_active:
        raise ConnectionRefusedError('Invalid authentication')
    
    # Store user info in session
    await sio.save_session(sid, {
        'user_id': str(user.id),
        'username': user.username,
        'role': user.role
    })
    
    # Subscribe to dashboard room (global events)
    await sio.enter_room(sid, 'dashboard')
    
    print(f"Client {sid} connected as {user.username}")

@sio.event
async def disconnect(sid):
    """Handle disconnection"""
    session = await sio.get_session(sid)
    username = session.get('username', 'unknown') if session else 'unknown'
    print(f"Client {sid} ({username}) disconnected")

@sio.event
async def subscribe(sid, data):
    """Subscribe to a specific room (agent, task, or conversation)"""
    room = data.get('room')
    if not room:
        await sio.emit('error', {'message': 'Room name required'}, to=sid)
        return
    
    # Validate room format
    valid_prefixes = ['agent:', 'task:', 'conversation:']
    if not any(room.startswith(prefix) for prefix in valid_prefixes):
        await sio.emit('error', {'message': 'Invalid room format'}, to=sid)
        return
    
    await sio.enter_room(sid, room)
    await sio.emit('subscribed', {'room': room}, to=sid)
    print(f"Client {sid} subscribed to {room}")

@sio.event
async def unsubscribe(sid, data):
    """Unsubscribe from a room"""
    room = data.get('room')
    if room:
        await sio.leave_room(sid, room)
        await sio.emit('unsubscribed', {'room': room}, to=sid)
        print(f"Client {sid} unsubscribed from {room}")

@sio.event
async def heartbeat(sid, data):
    """Client heartbeat acknowledgment"""
    await sio.emit('heartbeat_ack', {'timestamp': data.get('timestamp')}, to=sid)
