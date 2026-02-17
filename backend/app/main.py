from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.models import *
from app.routers import auth, agents, tasks, conversations, telegram
from app.websocket import sio, socket_app
from app.background import start_background_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("WebSocket server initialized at /ws")
    
    # Start background tasks
    asyncio.create_task(start_background_tasks())
    
    yield
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Mission Control API",
    version="1.0.0",
    description="Real-time agent orchestration and monitoring dashboard",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.io app
app.mount("/ws", socket_app)

# Include REST API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(telegram.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "websocket": "enabled"}


@app.get("/")
async def root():
    return {
        "message": "Mission Control API",
        "version": "1.0.0",
        "websocket_endpoint": "/ws"
    }
