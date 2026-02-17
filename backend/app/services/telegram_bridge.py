"""
Telegram Bridge Service
Bi-directional sync between dashboard and Telegram notifications.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models import User, Agent, Task
from app.services.telegram_bot import TelegramBotService, get_telegram_bot_service


class TelegramBridge:
    """Bridge between dashboard events and Telegram notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.bot = get_telegram_bot_service(db)
    
    async def notify_agent_status_change(
        self,
        agent_id: UUID,
        old_status: str,
        new_status: str
    ):
        """Notify subscribed users when agent status changes"""
        # Get users subscribed to this agent
        subscriptions = self.db.query(User).filter(
            User.agent_subscriptions.contains([str(agent_id)])
        ).all()
        
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        agent_name = agent.name if agent else str(agent_id)
        
        message = f"""
🤖 <b>Agent Status Changed</b>

<b>{agent_name}</b>
{old_status} → <b>{new_status}</b>
        """
        
        for user in subscriptions:
            if user.telegram_chat_id:
                await self.bot.send_message(user.telegram_chat_id, message)
    
    async def notify_task_completed(self, task_id: UUID, success: bool = True):
        """Notify when task completes"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        
        # Notify task creator
        creator = task.created_by_user
        if creator and creator.telegram_chat_id:
            status_emoji = "✅" if success else "❌"
            message = f"""
{status_emoji} <b>Task {('Completed' if success else 'Failed')}</b>

<b>{task.title}</b>

Status: {task.status.value}
Agent: {task.assigned_agent.name if task.assigned_agent else 'N/A'}
            """
            await self.bot.send_message(creator.telegram_chat_id, message)
    
    async def notify_system_alert(self, message: str, severity: str = "info"):
        """Broadcast system alert to all subscribed users"""
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨"
        }
        emoji = emoji_map.get(severity, "ℹ️")
        
        full_message = f"""
{emoji} <b>System Alert</b>

{message}
        """
        
        # Get all users with telegram linked
        users = self.db.query(User).filter(
            User.telegram_chat_id.isnot(None)
        ).all()
        
        for user in users:
            await self.bot.send_message(user.telegram_chat_id, full_message)
    
    async def send_daily_summary(self, user_id: UUID):
        """Send daily summary to user"""
        from app.services.agent_registry import AgentRegistryService
        from app.services.task_orchestrator import TaskOrchestratorService
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.telegram_chat_id:
            return
        
        agent_service = AgentRegistryService(self.db)
        task_service = TaskOrchestratorService(self.db)
        
        agent_stats = agent_service.get_agent_stats()
        task_stats = task_service.get_queue_stats()
        
        message = f"""
📊 <b>Daily Summary</b>

<b>Agents:</b>
🟢 Ready: {agent_stats.get('ready', 0)}
🔵 Busy: {agent_stats.get('busy', 0)}
🔴 Error: {agent_stats.get('error', 0)}

<b>Tasks (24h):</b>
✅ Completed: {task_stats.get('completed', 0)}
❌ Failed: {task_stats.get('failed', 0)}
⏳ Pending: {task_stats.get('pending', 0)}
        """
        
        await self.bot.send_message(user.telegram_chat_id, message)


def get_telegram_bridge(db: Session) -> TelegramBridge:
    return TelegramBridge(db)
