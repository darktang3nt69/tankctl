from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/aquarium"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "ultra-secure-key-here"
    PRE_SHARED_KEY: str = "your-secret-key"
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 600
    RATE_LIMIT_PER_HOUR: int = 10000
    
    # Discord
    DISCORD_WEBHOOK_URL: Optional[str] = None
    DISCORD_ENABLED: bool = False
    
    # Application
    DEBUG: bool = False
    APP_NAME: str = "TankCTL"
    APP_VERSION: str = "1.0.0"
    
    # Flower
    FLOWER_BASIC_AUTH: str = "admin:admin"
    FLOWER_UNAUTHENTICATED_API: bool = True
    FLOWER_URL_PREFIX: str = "flower"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"  # Allow extra fields in the .env file
    )

settings = Settings() 