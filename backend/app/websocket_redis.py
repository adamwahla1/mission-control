"""
Redis adapter for scaling WebSocket across multiple nodes.
Enable this when deploying to production with multiple backend instances.
"""

import socketio
from app.config import settings

# Redis manager for multi-node scaling
def create_redis_manager():
    """Create Redis manager for Socket.io"""
    return socketio.AsyncRedisManager(settings.REDIS_URL)

# Use this when creating sio in websocket.py:
# sio = socketio.AsyncServer(
#     async_mode='asgi',
#     client_manager=create_redis_manager(),
#     ...
# )
