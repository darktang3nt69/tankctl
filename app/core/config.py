from pydantic_settings import BaseSettings

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

    # Tank
    TANK_PRESHARED_KEY: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_BACKEND_URL: str
    celery_result_backend: str

    # Heartbeat Monitor
    HEARTBEAT_CHECK_INTERVAL_MINUTES: int =1
    TANK_OFFLINE_THRESHOLD_MINUTES: int = 2
    SCHEDULE_LIGHTING_INTERVAL_MINUTES: int = 2
    CHECK_OFFLINE_TANK_STATUS_INTERVAL_MINUTES: int = 5

    # Discord (later)
    DISCORD_WEBHOOK_URL: str

    # Admin API key
    ADMIN_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
