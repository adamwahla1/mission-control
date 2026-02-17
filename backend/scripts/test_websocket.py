"""
Test WebSocket connection and events
Usage: python scripts/test_websocket.py
"""

import asyncio
import socketio

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("Connected to server")
    await sio.emit('subscribe', {'room': 'agent:123'})

@sio.event
async def disconnect():
    print("Disconnected from server")

@sio.on('agent:status_changed')
async def on_agent_status(data):
    print(f"Agent status changed: {data}")

@sio.on('task:created')
async def on_task_created(data):
    print(f"Task created: {data}")

@sio.on('task:assigned')
async def on_task_assigned(data):
    print(f"Task assigned: {data}")

@sio.on('task:updated')
async def on_task_updated(data):
    print(f"Task updated: {data}")

@sio.on('task:completed')
async def on_task_completed(data):
    print(f"Task completed: {data}")

@sio.on('conversation:message')
async def on_conversation_message(data):
    print(f"New message: {data}")

@sio.on('system:alert')
async def on_system_alert(data):
    print(f"System alert: {data}")

@sio.on('subscribed')
async def on_subscribed(data):
    print(f"Subscribed to room: {data}")

@sio.on('unsubscribed')
async def on_unsubscribed(data):
    print(f"Unsubscribed from room: {data}")

@sio.on('heartbeat_ack')
async def on_heartbeat_ack(data):
    print(f"Heartbeat acknowledged: {data}")

@sio.on('error')
async def on_error(data):
    print(f"Error: {data}")

async def main():
    import sys
    
    # Get token from command line or use default
    token = sys.argv[1] if len(sys.argv) > 1 else 'your-jwt-token-here'
    
    print(f"Connecting to WebSocket server...")
    print(f"Using token: {token[:20]}..." if len(token) > 20 else f"Using token: {token}")
    
    try:
        # Connect with auth token
        await sio.connect(
            'http://localhost:8000',
            auth={'token': token},
            namespaces=['/']
        )
        
        # Send a heartbeat
        await sio.emit('heartbeat', {'timestamp': asyncio.get_event_loop().time()})
        
        # Keep connection alive
        print("Connected! Listening for events for 60 seconds...")
        print("Press Ctrl+C to disconnect")
        await asyncio.sleep(60)
        
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDisconnected by user")
