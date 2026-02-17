from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models import Task, TaskStatus, User
from app.schemas.task import TaskCreate, TaskResponse, TaskAssignRequest
from app.services.event_bus import event_bus

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    status: str | None = Query(None),
    agent_id: UUID | None = Query(None),
    priority: str | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Task)
    
    # Non-admin users can only see their own tasks
    if current_user.role not in ['super_admin', 'agent_manager']:
        query = query.filter(Task.created_by_id == current_user.id)
    
    if status:
        query = query.filter(Task.status == status)
    if agent_id:
        query = query.filter(Task.agent_id == agent_id)
    if priority:
        query = query.filter(Task.priority == priority)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check authorization
    if current_user.role not in ['super_admin', 'agent_manager']:
        if task.created_by_id != current_user.id and task.agent_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this task")
    
    return task

@router.post("/", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_task = Task(**task.model_dump(), created_by_id=current_user.id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: UUID,
    assign: TaskAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.PENDING:
        raise HTTPException(status_code=400, detail="Task already assigned")
    
    from datetime import datetime
    task.agent_id = assign.agent_id
    task.status = TaskStatus.ASSIGNED
    task.assigned_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    # Broadcast assignment
    await event_bus.broadcast_task_assigned(
        task_id=task.id,
        agent_id=assign.agent_id,
        task_data={
            'title': task.title,
            'priority': task.priority.value,
            'status': task.status.value
        }
    )
    
    return task

@router.post("/{task_id}/cancel")
def cancel_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed/failed task")
    
    task.status = TaskStatus.CANCELLED
    db.commit()
    return {"message": "Task cancelled"}
