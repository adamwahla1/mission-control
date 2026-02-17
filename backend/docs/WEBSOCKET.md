# WebSocket API Documentation

## Connection

Connect to `ws://localhost:8000/ws` with JWT token:

```javascript
const socket = io('ws://localhost:8000', {
  auth: { token: 'your-jwt-token' },
  path: '/ws'
});
```

## Events

### Client → Server

| Event | Data | Description |
|-------|------|-------------|
| `subscribe` | `{room: "agent:123"}` | Subscribe to room |
| `unsubscribe` | `{room: "agent:123"}` | Unsubscribe from room |
| `heartbeat` | `{timestamp: 1234567890}` | Client heartbeat |

### Server → Client

| Event | Data | Description |
|-------|------|-------------|
| `agent:status_changed` | `{agent_id, old_status, new_status, timestamp}` | Agent status change |
| `agent:heartbeat` | `{agent_id, timestamp, metadata}` | Agent heartbeat |
| `task:created` | `{task_id, task, timestamp}` | New task created |
| `task:assigned` | `{task_id, agent_id, task, timestamp}` | Task assigned |
| `task:updated` | `{task_id, update, timestamp}` | Task progress update |
| `task:completed` | `{task_id, result, timestamp}` | Task completed |
| `conversation:message` | `{conversation_id, message, timestamp}` | New message |
| `system:alert` | `{message, severity, timestamp}` | System alert |
| `subscribed` | `{room}` | Room subscription confirmation |
| `unsubscribed` | `{room}` | Room unsubscription confirmation |
| `heartbeat_ack` | `{timestamp}` | Heartbeat acknowledgment |
| `error` | `{message}` | Error message |

## Rooms

- `dashboard` - Global events (auto-subscribed on connect)
- `agent:{id}` - Agent-specific events
- `task:{id}` - Task-specific events
- `conversation:{id}` - Conversation messages

## Authentication

All WebSocket connections require a valid JWT token passed in the `auth` object during connection:

```javascript
const socket = io('ws://localhost:8000', {
  auth: { token: 'your-jwt-token' },
  path: '/ws'
});
```

If the token is invalid or missing, the connection will be refused.

## Usage Examples

### Subscribe to Agent Events

```javascript
socket.emit('subscribe', { room: 'agent:123e4567-e89b-12d3-a456-426614174000' });

socket.on('agent:status_changed', (data) => {
  console.log(`Agent ${data.agent_id} changed from ${data.old_status} to ${data.new_status}`);
});
```

### Subscribe to Task Events

```javascript
socket.emit('subscribe', { room: 'task:123e4567-e89b-12d3-a456-426614174000' });

socket.on('task:updated', (data) => {
  console.log(`Task ${data.task_id} updated:`, data.update);
});
```

### Heartbeat

```javascript
// Send heartbeat every 25 seconds
setInterval(() => {
  socket.emit('heartbeat', { timestamp: Date.now() });
}, 25000);

socket.on('heartbeat_ack', (data) => {
  console.log('Server acknowledged heartbeat');
});
```

## Python Client Example

```python
import asyncio
import socketio

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("Connected!")
    await sio.emit('subscribe', {'room': 'agent:123'})

@sio.on('agent:status_changed')
async def on_status_change(data):
    print(f"Status changed: {data}")

async def main():
    await sio.connect(
        'http://localhost:8000',
        auth={'token': 'your-jwt-token'},
        namespaces=['/']
    )
    await asyncio.sleep(60)
    await sio.disconnect()

asyncio.run(main())
```

## Scaling with Redis

For production deployments with multiple backend instances, enable the Redis adapter:

```python
# In app/websocket.py, uncomment the Redis manager:
from app.websocket_redis import create_redis_manager

sio = socketio.AsyncServer(
    async_mode='asgi',
    client_manager=create_redis_manager(),
    cors_allowed_origins=settings.CORS_ORIGINS,
    ping_timeout=30,
    ping_interval=25,
    max_http_buffer_size=1_000_000
)
```

This ensures events are broadcast across all server instances.
