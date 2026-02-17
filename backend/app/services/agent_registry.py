"""
Agent Registry Service
Manages agent lifecycle, discovery, heartbeat, and state transitions.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Agent, AgentStatus, AgentType, AgentStateTransition
from app.services.event_bus import event_bus


class AgentRegistryService:
    def __init__(self, db: Session):
        self.db = db
    
    def register_agent(
        self,
        name: str,
        agent_type: AgentType = AgentType.SUBAGENT,
        capabilities: List[str] = None,
        config: Dict[str, Any] = None,
        parent_id: UUID = None
    ) -> Agent:
        """Register a new agent in the system"""
        agent = Agent(
            name=name,
            agent_type=agent_type,
            status=AgentStatus.IDLE,
            capabilities=capabilities or [],
            config=config or {},
            parent_id=parent_id
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent
    
    def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        """Get agent by ID"""
        return self.db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.deleted_at.is_(None)
        ).first()
    
    def list_agents(
        self,
        status: AgentStatus = None,
        agent_type: AgentType = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Agent]:
        """List agents with optional filters"""
        query = self.db.query(Agent).filter(Agent.deleted_at.is_(None))
        
        if status:
            query = query.filter(Agent.status == status)
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        
        return query.offset(skip).limit(limit).all()
    
    async def heartbeat(
        self,
        agent_id: UUID,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Process agent heartbeat"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        # Update heartbeat timestamp
        agent.last_heartbeat = datetime.utcnow()
        
        # If agent was offline, mark as ready
        if agent.status == AgentStatus.OFFLINE:
            await self.transition_state(agent_id, AgentStatus.READY, "heartbeat_recovery")
        
        self.db.commit()
        
        # Broadcast heartbeat
        await event_bus.broadcast_agent_heartbeat(agent_id, metadata or {})
        return True
    
    async def transition_state(
        self,
        agent_id: UUID,
        new_status: AgentStatus,
        reason: str = None,
        triggered_by: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Transition agent to new state with validation"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        old_status = agent.status
        
        # Validate transition (simplified - should use StateMachine)
        valid_transitions = {
            AgentStatus.IDLE: [AgentStatus.INITIALIZING],
            AgentStatus.INITIALIZING: [AgentStatus.READY, AgentStatus.ERROR],
            AgentStatus.READY: [AgentStatus.BUSY, AgentStatus.PAUSED, AgentStatus.SHUTTING_DOWN],
            AgentStatus.BUSY: [AgentStatus.READY, AgentStatus.ERROR, AgentStatus.PAUSED],
            AgentStatus.PAUSED: [AgentStatus.READY, AgentStatus.BUSY, AgentStatus.SHUTTING_DOWN],
            AgentStatus.ERROR: [AgentStatus.INITIALIZING, AgentStatus.SHUTTING_DOWN],
            AgentStatus.SHUTTING_DOWN: [AgentStatus.OFFLINE],
            AgentStatus.OFFLINE: [AgentStatus.INITIALIZING]
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise ValueError(f"Invalid transition from {old_status} to {new_status}")
        
        # Update agent
        agent.previous_status = old_status
        agent.status = new_status
        
        self.db.commit()
        
        # Record transition
        transition = AgentStateTransition(
            agent_id=agent_id,
            from_status=old_status.value,
            to_status=new_status.value,
            reason=reason,
            metadata=metadata or {},
            triggered_by=triggered_by
        )
        self.db.add(transition)
        self.db.commit()
        
        # Broadcast event
        await event_bus.broadcast_agent_status_change(
            agent_id=agent_id,
            old_status=old_status.value,
            new_status=new_status.value,
            metadata={'reason': reason, 'triggered_by': triggered_by}
        )
        
        return True
    
    def get_stale_agents(self, timeout_seconds: int = 30) -> List[Agent]:
        """Get agents that haven't sent heartbeat within timeout"""
        cutoff = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        return self.db.query(Agent).filter(
            Agent.status.in_([AgentStatus.READY, AgentStatus.BUSY]),
            Agent.last_heartbeat < cutoff,
            Agent.deleted_at.is_(None)
        ).all()
    
    async def mark_stale_agents_offline(self, timeout_seconds: int = 30):
        """Mark stale agents as offline"""
        stale_agents = self.get_stale_agents(timeout_seconds)
        for agent in stale_agents:
            await self.transition_state(
                agent.id,
                AgentStatus.OFFLINE,
                reason="heartbeat_timeout",
                triggered_by="system"
            )
        return len(stale_agents)
    
    def get_agent_stats(self) -> Dict[str, int]:
        """Get count of agents by status"""
        stats = self.db.query(
            Agent.status,
            func.count(Agent.id)
        ).filter(
            Agent.deleted_at.is_(None)
        ).group_by(Agent.status).all()
        
        return {status.value: count for status, count in stats}
    
    def find_agents_by_capability(self, capability: str) -> List[Agent]:
        """Find agents with specific capability"""
        return self.db.query(Agent).filter(
            Agent.capabilities.contains([capability]),
            Agent.status.in_([AgentStatus.READY, AgentStatus.IDLE]),
            Agent.deleted_at.is_(None)
        ).all()
