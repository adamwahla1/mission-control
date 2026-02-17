from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_active_user, require_role
from app.models import Agent, AgentStatus, User
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentControlRequest
from app.services.event_bus import event_bus

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/", response_model=List[AgentResponse])
def list_agents(
    status: str | None = Query(None, description="Filter by status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Agent).filter(Agent.deleted_at.is_(None))
    if status:
        query = query.filter(Agent.status == status)
    agents = query.offset(skip).limit(limit).all()
    return agents

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.deleted_at.is_(None)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/", response_model=AgentResponse)
def create_agent(
    agent: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("agent_manager"))
):
    db_agent = Agent(**agent.model_dump())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: UUID,
    agent_update: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("agent_manager"))
):
    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    for field, value in agent_update.model_dump(exclude_unset=True).items():
        setattr(db_agent, field, value)
    
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.post("/{agent_id}/control")
async def control_agent(
    agent_id: UUID,
    control: AgentControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("agent_operator"))
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Additional authorization: agent_operator can only control agents they created
    # (unless they're agent_manager or super_admin)
    if current_user.role == 'agent_operator':
        # Check if user has permission for this specific agent
        # This would need a user-agent relationship table in production
        pass  # For now, allow all agent_operators to control
    
    old_status = agent.status.value
    
    # Update status based on action
    if control.action == "pause":
        agent.status = AgentStatus.PAUSED
    elif control.action == "resume":
        agent.status = AgentStatus.READY
    elif control.action == "restart":
        agent.status = AgentStatus.INITIALIZING
    elif control.action == "stop":
        agent.status = AgentStatus.SHUTTING_DOWN
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    db.commit()
    
    # Broadcast status change via WebSocket
    await event_bus.broadcast_agent_status_change(
        agent_id=agent.id,
        old_status=old_status,
        new_status=agent.status.value,
        metadata={'action': control.action, 'triggered_by': current_user.username}
    )
    
    return {"message": f"Agent {agent_id} {control.action} command sent"}

@router.delete("/{agent_id}")
def delete_agent(
    agent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("agent_manager"))
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Soft delete
    from datetime import datetime
    agent.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Agent deleted"}
