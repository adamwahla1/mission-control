from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Import all models to register with Base
from app.models import (
    User,
    Agent,
    AgentStateTransition,
    Task,
    Conversation,
    Message,
    AuditLog,
    DeadLetterQueue,
    RetentionPolicy,
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
