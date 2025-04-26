"""
Configuration settings for the application.

This module contains the settings class that loads configuration from environment variables.
"""

from typing import Dict, List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    APP_NAME: str = "TankCtl"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "changeme"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/tankctl"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/tankctl"
    
    # Redis settings
    REDIS_URL: str = "redis://:changeme@redis:6379/0"
    
    # Discord settings - Enabled by default
    DISCORD_WEBHOOK_URL: Optional[str] = None
    DISCORD_ENABLED: bool = True
    
    # Tank settings
    DEFAULT_TANK_CONFIG: Dict = Field(default_factory=dict)
    MAX_TANK_NAME_LENGTH: int = 100
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # File storage settings
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Security
    PRE_SHARED_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="allow")

settings = Settings()