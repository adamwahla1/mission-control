"""
Background task scheduler for periodic maintenance.
"""

import asyncio
from datetime import datetime
from app.database import SessionLocal
from app.services.agent_registry import AgentRegistryService
from app.services.task_orchestrator import TaskOrchestratorService


async def heartbeat_monitor_loop():
    """Periodically check for stale agents and tasks"""
    while True:
        try:
            db = SessionLocal()
            try:
                # Check agents
                agent_service = AgentRegistryService(db)
                stale_count = await agent_service.mark_stale_agents_offline(timeout_seconds=30)
                if stale_count > 0:
                    print(f"[{datetime.utcnow()}] Marked {stale_count} agents as offline")
                
                # Check tasks
                task_service = TaskOrchestratorService(db)
                reclaimed = await task_service.reclaim_stale_tasks(timeout_seconds=30)
                if reclaimed > 0:
                    print(f"[{datetime.utcnow()}] Reclaimed {reclaimed} stale tasks")
                    
            finally:
                db.close()
        except Exception as e:
            print(f"Error in heartbeat monitor: {e}")
        
        # Run every 10 seconds
        await asyncio.sleep(10)


async def start_background_tasks():
    """Start all background tasks"""
    await asyncio.gather(
        heartbeat_monitor_loop()
    )
