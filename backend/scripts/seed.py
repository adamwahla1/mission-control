#!/usr/bin/env python3
"""
Database seed script for Mission Control.
Creates sample data for testing and development.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, engine, Base
from app.models import User, Agent, Task, AgentType, AgentStatus, TaskStatus, Priority
from app.config import settings
import uuid
from datetime import datetime


def seed_database():
    """Seed the database with sample data."""
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if already seeded
        existing = db.query(Agent).first()
        if existing:
            print("Database already has data. Skipping seed.")
            return

        print("Seeding database with sample agents...")
        
        # Create sample agents
        agent1 = Agent(
            id=uuid.uuid4(),
            name="Research Assistant",
            agent_type=AgentType.SUBAGENT,
            status=AgentStatus.READY,
            capabilities=["research", "summarize", "web_search"],
            config={"max_concurrent_tasks": 3}
        )
        
        agent2 = Agent(
            id=uuid.uuid4(),
            name="Code Reviewer",
            agent_type=AgentType.SUBAGENT,
            status=AgentStatus.IDLE,
            capabilities=["code_review", "linting", "security_scan"],
            config={"languages": ["python", "typescript", "rust"]}
        )
        
        agent3 = Agent(
            id=uuid.uuid4(),
            name="Main Orchestrator",
            agent_type=AgentType.MAIN,
            status=AgentStatus.BUSY,
            capabilities=["orchestration", "task_routing", "monitoring"],
            config={"auto_scaling": True}
        )
        
        db.add_all([agent1, agent2, agent3])
        db.commit()
        
        print(f"Created {db.query(Agent).count()} sample agents")
        print("Database seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
