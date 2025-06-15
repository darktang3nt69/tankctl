from pydantic_settings import BaseSettings
from pydantic import Field, validator, field_validator # Import Field, validator, and field_validator

class Settings(BaseSettings):
    # Database
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # SQLAlchemy Connection Pool Settings
    SQLALCHEMY_POOL_SIZE: int = 10
    SQLALCHEMY_MAX_OVERFLOW: int = 20
    SQLALCHEMY_POOL_RECYCLE: int = 1800 # 30 minutes
    SQLALCHEMY_POOL_TIMEOUT: int = 30

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=10080, description="Refresh token expiration in minutes (7 days)")
    REFRESH_TOKEN_SECRET_KEY: str = Field(default="", description="Secret key for signing refresh tokens")

    # Admin API Key
    ADMIN_API_KEY: str = ""

    # Tank
    TANK_PRESHARED_KEY: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_BACKEND_URL: str
    celery_result_backend: str

    # Heartbeat Monitor
    HEARTBEAT_CHECK_INTERVAL_MINUTES: int = 1
    TANK_OFFLINE_THRESHOLD_MINUTES: int = 2

    # Discord (later)
    DISCORD_WEBHOOK_URL: str

    # Redis for SSE
    REDIS_URL: str

    # Logging
    LOG_LEVEL: str = "INFO" # Default to INFO, but can be overridden

    # Web Push settings
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_CLAIMS_EMAIL: str = ""

    @field_validator("VAPID_PUBLIC_KEY", "VAPID_PRIVATE_KEY", "VAPID_CLAIMS_EMAIL", mode='before')
    @classmethod
    def validate_vapid_keys(cls, v, info):
        if not v and info.field_name in ["VAPID_PUBLIC_KEY", "VAPID_PRIVATE_KEY", "VAPID_CLAIMS_EMAIL"]:
            raise ValueError(f"{info.field_name} must be set for Web Push notifications")
        return v

    @field_validator("ADMIN_API_KEY", mode='before')
    @classmethod
    def validate_admin_api_key(cls, v, info):
        if not v:
            raise ValueError(f"{info.field_name} must be set")
        return v

    class Config:
        env_file = ".env"

settings = Settings()
