"""
Task Orchestrator Service
Manages task lifecycle, assignment, and execution.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Task, TaskStatus, Priority, Agent
from app.services.event_bus import event_bus
from app.services.agent_registry import AgentRegistryService


class TaskOrchestratorService:
    def __init__(self, db: Session):
        self.db = db
        self.agent_registry = AgentRegistryService(db)
    
    async def create_task(
        self,
        title: str,
        description: str = None,
        priority: Priority = Priority.MEDIUM,
        payload: Dict[str, Any] = None,
        created_by_id: UUID = None,
        parent_task_id: UUID = None
    ) -> Task:
        """Create a new task"""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            payload=payload or {},
            status=TaskStatus.PENDING,
            created_by_id=created_by_id,
            parent_task_id=parent_task_id
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # Broadcast task creation
        await event_bus.broadcast_task_created(
            task_id=task.id,
            task_data={
                'title': task.title,
                'priority': task.priority.value,
                'status': task.status.value
            }
        )
        
        return task
    
    def get_task(self, task_id: UUID) -> Optional[Task]:
        """Get task by ID"""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def list_tasks(
        self,
        status: TaskStatus = None,
        agent_id: UUID = None,
        priority: Priority = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """List tasks with optional filters"""
        query = self.db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        if agent_id:
            query = query.filter(Task.agent_id == agent_id)
        if priority:
            query = query.filter(Task.priority == priority)
        
        return query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
    
    async def assign_task(self, task_id: UUID, agent_id: UUID) -> Task:
        """Assign task to agent with atomic claim"""
        # Use ORM instead of raw SQL
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.status == TaskStatus.PENDING
        ).with_for_update().first()

        if not task:
            raise ValueError("Task not found or already assigned")

        task.agent_id = agent_id
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.utcnow()
        task.claimed_at = datetime.utcnow()
        task.version += 1

        self.db.commit()
        self.db.refresh(task)

        # Broadcast assignment
        await event_bus.broadcast_task_assigned(
            task_id=task.id,
            agent_id=agent_id,
            task_data={
                'title': task.title,
                'priority': task.priority.value,
                'status': task.status.value
            }
        )
        return task
    
    async def claim_next_task(self, agent_id: UUID) -> Optional[Task]:
        """Agent claims next available task from queue"""
        # Get agent capabilities
        agent = self.agent_registry.get_agent(agent_id)
        if not agent:
            return None

        # Use SQLAlchemy with_for_update for atomic claim
        task = self.db.query(Task).filter(
            Task.status == TaskStatus.PENDING
        ).order_by(
            Task.priority.desc(),
            Task.created_at.asc()
        ).with_for_update(skip_locked=True).first()

        if not task:
            return None

        task.agent_id = agent_id
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.utcnow()
        task.claimed_at = datetime.utcnow()
        task.version += 1

        self.db.commit()
        self.db.refresh(task)

        await event_bus.broadcast_task_assigned(
            task_id=task.id,
            agent_id=agent_id,
            task_data={
                'title': task.title,
                'priority': task.priority.value,
                'status': task.status.value
            }
        )
        return task
    
    async def start_task(self, task_id: UUID, agent_id: UUID) -> Task:
        """Mark task as running"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        
        if task.agent_id != agent_id:
            raise ValueError("Task not assigned to this agent")
        
        if task.status != TaskStatus.ASSIGNED:
            raise ValueError(f"Task cannot be started (status: {task.status})")
        
        task.status = TaskStatus.RUNNING
        task.last_heartbeat = datetime.utcnow()
        self.db.commit()
        
        await event_bus.broadcast_task_updated(
            task_id=task.id,
            update_data={'status': TaskStatus.RUNNING.value, 'started_at': datetime.utcnow().isoformat()}
        )
        
        return task
    
    async def complete_task(
        self,
        task_id: UUID,
        agent_id: UUID,
        result: Dict[str, Any]
    ) -> Task:
        """Mark task as completed with idempotency"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        
        if task.agent_id != agent_id:
            raise ValueError("Task not assigned to this agent")
        
        # Idempotency: if already completed, return success
        if task.status == TaskStatus.COMPLETED:
            return task
        
        if task.status != TaskStatus.RUNNING:
            raise ValueError(f"Task cannot be completed (status: {task.status})")
        
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.utcnow()
        self.db.commit()
        
        await event_bus.broadcast_task_completed(
            task_id=task.id,
            result=result
        )
        
        return task
    
    async def fail_task(
        self,
        task_id: UUID,
        agent_id: UUID,
        error: str
    ) -> Task:
        """Mark task as failed"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        
        if task.agent_id != agent_id:
            raise ValueError("Task not assigned to this agent")
        
        task.status = TaskStatus.FAILED
        task.result = {'error': error}
        task.completed_at = datetime.utcnow()
        self.db.commit()
        
        await event_bus.broadcast_task_updated(
            task_id=task.id,
            update_data={'status': TaskStatus.FAILED.value, 'error': error}
        )
        
        return task
    
    async def cancel_task(self, task_id: UUID) -> Task:
        """Cancel a pending or assigned task"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            raise ValueError("Cannot cancel completed/failed task")
        
        task.status = TaskStatus.CANCELLED
        self.db.commit()
        
        return task
    
    def send_heartbeat(self, task_id: UUID, agent_id: UUID):
        """Update task heartbeat to prevent reclamation"""
        task = self.get_task(task_id)
        if task and task.agent_id == agent_id:
            task.last_heartbeat = datetime.utcnow()
            self.db.commit()
    
    def get_stale_tasks(self, timeout_seconds: int = 30) -> List[Task]:
        """Get tasks that haven't sent heartbeat within timeout"""
        cutoff = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        return self.db.query(Task).filter(
            Task.status.in_([TaskStatus.ASSIGNED, TaskStatus.RUNNING]),
            Task.last_heartbeat < cutoff
        ).all()
    
    async def reclaim_stale_tasks(self, timeout_seconds: int = 30) -> int:
        """Reclaim stale tasks and return to pending"""
        stale_tasks = self.get_stale_tasks(timeout_seconds)
        count = 0
        
        for task in stale_tasks:
            task.status = TaskStatus.PENDING
            task.agent_id = None
            task.reclaim_count += 1
            count += 1
        
        self.db.commit()
        return count
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get task counts by status"""
        stats = self.db.query(
            Task.status,
            func.count(Task.id)
        ).group_by(Task.status).all()
        
        return {status.value: count for status, count in stats}
