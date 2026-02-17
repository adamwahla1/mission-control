"""
Telegram Webhook Router
Handles incoming updates from Telegram Bot API.
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.config import settings
from app.services.telegram_bot import get_telegram_bot_service, TelegramBotService

router = APIRouter(prefix="/telegram", tags=["telegram"])

@router.post("/webhook/{bot_token}")
async def telegram_webhook(
    request: Request,
    bot_token: str,
    x_telegram_bot_api_secret_token: str = Header(None),
    db: Session = Depends(get_db)
):
    """Handle incoming Telegram webhook"""
    # Verify webhook secret (prevents spoofing)
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid webhook secret")
    
    # Verify bot token matches first part of actual token
    expected_prefix = settings.TELEGRAM_BOT_TOKEN.split(':')[0] if settings.TELEGRAM_BOT_TOKEN else None
    if not expected_prefix or bot_token != expected_prefix:
        raise HTTPException(status_code=403, detail="Invalid bot token")
    
    # Also verify the full token is configured
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Bot not configured")
    
    # Parse update
    update = await request.json()
    
    # Initialize bot service
    bot_service = get_telegram_bot_service(db)
    
    # Handle message
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        username = message['from'].get('username', 'Unknown')
        
        # Parse command
        if text.startswith('/'):
            parts = text.split()
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            await handle_command(bot_service, command, args, chat_id, username)
        else:
            # Echo for non-commands
            await bot_service.send_message(chat_id, f"You said: {text}")
    
    # Handle callback queries (for inline keyboards)
    elif 'callback_query' in update:
        callback = update['callback_query']
        # Handle button clicks
        pass
    
    return {"ok": True}

async def handle_command(
    bot_service: TelegramBotService,
    command: str,
    args: list,
    chat_id: int,
    username: str
):
    """Route commands to appropriate handlers"""
    
    if command == '/start':
        await bot_service.cmd_start(chat_id, username)
    
    elif command == '/help':
        await bot_service.cmd_help(chat_id)
    
    elif command == '/agents':
        await bot_service.cmd_agents(chat_id)
    
    elif command == '/agent':
        if args:
            await bot_service.cmd_agent(chat_id, args[0])
        else:
            await bot_service.send_message(chat_id, "Usage: /agent <id>")
    
    elif command == '/tasks':
        await bot_service.cmd_tasks(chat_id)
    
    elif command == '/task':
        if args:
            await bot_service.cmd_task(chat_id, args[0])
        else:
            await bot_service.send_message(chat_id, "Usage: /task <id>")
    
    elif command == '/assign':
        # Parse: /assign <task_id> to <agent_id>
        if len(args) >= 3 and args[1].lower() == 'to':
            await bot_service.cmd_assign(chat_id, args[0], args[2])
        else:
            await bot_service.send_message(
                chat_id,
                "Usage: /assign <task_id> to <agent_id>"
            )
    
    elif command == '/status':
        await bot_service.cmd_status(chat_id)
    
    elif command == '/alert':
        if args:
            await bot_service.cmd_alert(chat_id, ' '.join(args))
        else:
            await bot_service.send_message(chat_id, "Usage: /alert <message>")
    
    else:
        await bot_service.send_message(chat_id, f"Unknown command: {command}\nUse /help for available commands.")

@router.post("/webhook/setup")
async def setup_webhook():
    """Setup webhook with Telegram (admin only)"""
    import httpx
    
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={
            "url": settings.TELEGRAM_WEBHOOK_URL,
            "allowed_updates": ["message", "callback_query"]
        })
    
    return response.json()

@router.get("/webhook/info")
async def get_webhook_info():
    """Get current webhook info from Telegram"""
    import httpx
    
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    
    return response.json()

@router.delete("/webhook/delete")
async def delete_webhook():
    """Delete webhook from Telegram"""
    import httpx
    
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteWebhook"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    
    return response.json()
