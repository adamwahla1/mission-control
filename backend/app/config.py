import os
import secrets

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://mcuser:mcpass@localhost:5432/missioncontrol"
    REDIS_URL: str = "redis://localhost:6379"
    # In production, this MUST be set via environment variable
    # Generate a secure secret with: python -c "import secrets; print(secrets.token_hex(32))"
    JWT_SECRET: str = os.getenv("JWT_SECRET", secrets.token_hex(32))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    RATE_LIMIT_RPM: int = 100
    HEARTBEAT_TIMEOUT: int = 30
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = ""  # Set via environment variable
    TELEGRAM_WEBHOOK_URL: str = "https://your-domain.com/api/v1/telegram/webhook"
    TELEGRAM_WEBHOOK_SECRET: str = ""  # For webhook validation
    
    class Config:
        env_file = ".env"

settings = Settings()
