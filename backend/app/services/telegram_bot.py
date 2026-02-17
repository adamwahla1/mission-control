"""
Telegram Bot Service
Handles bot commands and sends notifications to Telegram users.
"""

import httpx
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, Agent, Task
from app.services.agent_registry import AgentRegistryService
from app.services.task_orchestrator import TaskOrchestratorService


class TelegramBotService:
    API_BASE = "https://api.telegram.org/bot"
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_service = AgentRegistryService(db)
        self.task_service = TaskOrchestratorService(db)
        self.token = settings.TELEGRAM_BOT_TOKEN
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML"):
        """Send message to Telegram chat"""
        if not self.token:
            return
        
        url = f"{self.API_BASE}{self.token}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            })
    
    async def send_notification(self, user_id: UUID, message: str):
        """Send notification to user's Telegram"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and hasattr(user, 'telegram_chat_id') and user.telegram_chat_id:
            await self.send_message(user.telegram_chat_id, message)
    
    # Command Handlers
    
    async def cmd_start(self, chat_id: int, username: str):
        """Handle /start command"""
        welcome_text = f"""
👋 Welcome <b>{username}</b> to Mission Control!

Available commands:
/agents - List all agents
/agent &lt;id&gt; - Get agent details
/tasks - List recent tasks
/task &lt;id&gt; - Get task details
/status - System status
/help - Show this help

🔗 Link your account on the web dashboard to receive notifications.
        """
        await self.send_message(chat_id, welcome_text)
    
    async def cmd_help(self, chat_id: int):
        """Handle /help command"""
        help_text = """
<b>🤖 Mission Control Bot Commands</b>

<b>Agents:</b>
/agents - List all agents with status
/agent &lt;id&gt; - Get detailed agent info

<b>Tasks:</b>
/tasks - List recent tasks
/task &lt;id&gt; - Get task details
/assign &lt;task_id&gt; to &lt;agent_id&gt; - Assign task

<b>System:</b>
/status - System health overview
/alert &lt;message&gt; - Broadcast alert

<b>Notifications:</b>
You'll receive alerts for:
• Agent status changes
• Task completions/failures
• System warnings
        """
        await self.send_message(chat_id, help_text)
    
    async def cmd_agents(self, chat_id: int):
        """Handle /agents command"""
        agents = self.agent_service.list_agents(limit=20)
        
        if not agents:
            await self.send_message(chat_id, "No agents registered.")
            return
        
        status_emoji = {
            'online': '🟢',
            'busy': '🔵',
            'error': '🔴',
            'offline': '⚫',
            'idle': '⚪',
            'ready': '🟢',
            'paused': '🟡',
            'initializing': '🟠',
            'shutting_down': '🟤'
        }
        
        lines = ["<b>🤖 Agent Fleet</b>\n"]
        for agent in agents:
            emoji = status_emoji.get(agent.status.value, '⚪')
            lines.append(f"{emoji} <b>{agent.name}</b> (<code>{agent.id[:8]}</code>)")
            lines.append(f"   Status: {agent.status.value}")
            if agent.current_task:
                lines.append(f"   Task: {agent.current_task.title[:30]}...")
            lines.append("")
        
        await self.send_message(chat_id, "\n".join(lines))
    
    async def cmd_agent(self, chat_id: int, agent_id: str):
        """Handle /agent command"""
        try:
            agent_uuid = UUID(agent_id)
            agent = self.agent_service.get_agent(agent_uuid)
        except (ValueError, AttributeError):
            # Try partial match
            agent = self.db.query(Agent).filter(
                Agent.name.ilike(f"%{agent_id}%"),
                Agent.deleted_at.is_(None)
            ).first()
        
        if not agent:
            await self.send_message(chat_id, "❌ Agent not found.")
            return
        
        text = f"""
<b>🤖 {agent.name}</b>

<b>ID:</b> <code>{agent.id}</code>
<b>Type:</b> {agent.agent_type.value}
<b>Status:</b> {agent.status.value}
<b>Capabilities:</b> {', '.join(agent.capabilities) or 'None'}

<b>Current Task:</b>
{agent.current_task.title if agent.current_task else 'None'}

<b>Last Heartbeat:</b>
{agent.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S UTC') if agent.last_heartbeat else 'Never'}
        """
        await self.send_message(chat_id, text)
    
    async def cmd_tasks(self, chat_id: int):
        """Handle /tasks command"""
        tasks = self.task_service.list_tasks(limit=10)
        
        if not tasks:
            await self.send_message(chat_id, "No tasks found.")
            return
        
        status_emoji = {
            'pending': '⏳',
            'assigned': '👤',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '🚫'
        }
        
        lines = ["<b>📋 Recent Tasks</b>\n"]
        for task in tasks:
            emoji = status_emoji.get(task.status.value, '⏳')
            lines.append(f"{emoji} <b>{task.title[:40]}</b>")
            lines.append(f"   Status: {task.status.value} | Priority: {task.priority.value}")
            if task.assigned_agent:
                lines.append(f"   Agent: {task.assigned_agent.name}")
            lines.append("")
        
        await self.send_message(chat_id, "\n".join(lines))
    
    async def cmd_task(self, chat_id: int, task_id: str):
        """Handle /task command"""
        try:
            task_uuid = UUID(task_id)
            task = self.task_service.get_task(task_uuid)
        except (ValueError, AttributeError):
            await self.send_message(chat_id, "❌ Invalid task ID.")
            return
        
        if not task:
            await self.send_message(chat_id, "❌ Task not found.")
            return
        
        text = f"""
<b>📋 {task.title}</b>

<b>ID:</b> <code>{task.id}</code>
<b>Status:</b> {task.status.value}
<b>Priority:</b> {task.priority.value}

<b>Description:</b>
{task.description or 'No description'}

<b>Assigned to:</b>
{task.assigned_agent.name if task.assigned_agent else 'Unassigned'}

<b>Created:</b> {task.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        await self.send_message(chat_id, text)
    
    async def cmd_assign(self, chat_id: int, task_id: str, agent_id: str):
        """Handle /assign command"""
        try:
            task_uuid = UUID(task_id)
            agent_uuid = UUID(agent_id)
        except ValueError:
            await self.send_message(chat_id, "❌ Invalid IDs. Use: /assign <task_id> to <agent_id>")
            return
        
        try:
            task = await self.task_service.assign_task(task_uuid, agent_uuid)
            await self.send_message(
                chat_id,
                f"✅ Task <b>{task.title}</b> assigned to agent <b>{task.assigned_agent.name}</b>"
            )
        except ValueError as e:
            await self.send_message(chat_id, f"❌ {str(e)}")
    
    async def cmd_status(self, chat_id: int):
        """Handle /status command"""
        agent_stats = self.agent_service.get_agent_stats()
        task_stats = self.task_service.get_queue_stats()
        
        text = f"""
<b>📊 System Status</b>

<b>Agents:</b>
🟢 Online/Ready: {agent_stats.get('ready', 0) + agent_stats.get('online', 0)}
🔵 Busy: {agent_stats.get('busy', 0)}
🔴 Error: {agent_stats.get('error', 0)}
⚫ Offline: {agent_stats.get('offline', 0)}

<b>Tasks:</b>
⏳ Pending: {task_stats.get('pending', 0)}
🔄 Running: {task_stats.get('running', 0)}
✅ Completed: {task_stats.get('completed', 0)}
❌ Failed: {task_stats.get('failed', 0)}
        """
        await self.send_message(chat_id, text)
    
    async def cmd_alert(self, chat_id: int, message: str):
        """Handle /alert command - broadcast to dashboard"""
        from app.services.event_bus import event_bus
        await event_bus.broadcast_system_alert(message, severity='warning')
        await self.send_message(chat_id, f"📢 Alert broadcast: {message}")


# Global instance for use in webhook handler
def get_telegram_bot_service(db: Session) -> TelegramBotService:
    return TelegramBotService(db)
