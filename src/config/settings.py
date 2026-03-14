"""
Configuration and settings for TankCtl backend.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from dataclasses import dataclass


@dataclass
class MQTTSettings:
    """MQTT broker configuration."""

    broker_host: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    username: str = os.getenv("MQTT_USERNAME", "")
    password: str = os.getenv("MQTT_PASSWORD", "")
    client_id: str = "tankctl-backend"
    qos: int = 1
    keepalive: int = 60


@dataclass
class DatabaseSettings:
    """PostgreSQL database configuration."""

    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "tankctl")
    username: str = os.getenv("POSTGRES_USER", "tankctl")
    password: str = os.getenv("POSTGRES_PASSWORD", "")

    @property
    def url(self) -> str:
        """SQLAlchemy database URL."""
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class TimescaleSettings:
    """TimescaleDB telemetry database configuration."""

    host: str = os.getenv("TIMESCALE_HOST", "localhost")
    port: int = int(os.getenv("TIMESCALE_PORT", "5432"))
    database: str = os.getenv("TIMESCALE_DB", "tankctl_telemetry")
    username: str = os.getenv("TIMESCALE_USER", "tankctl")
    password: str = os.getenv("TIMESCALE_PASSWORD", "")

    @property
    def url(self) -> str:
        """SQLAlchemy database URL for TimescaleDB."""
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class APISettings:
    """FastAPI configuration."""

    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


@dataclass
class SchedulerSettings:
    """APScheduler configuration."""

    enabled: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    # Seconds to wait before marking device offline
    device_offline_timeout: int = int(os.getenv("DEVICE_OFFLINE_TIMEOUT", "60"))
    # Seconds between shadow reconciliation runs (10s)
    shadow_reconciliation_interval: int = int(
        os.getenv("SHADOW_RECONCILIATION_INTERVAL", "10")
    )
    # Seconds between offline detection checks (30s)
    offline_detection_interval: int = int(
        os.getenv("OFFLINE_DETECTION_INTERVAL", "30")
    )



@dataclass
class AlertSettings:
    """Alert thresholds and suppression settings."""

    enabled: bool = os.getenv("ALERTS_ENABLED", "true").lower() == "true"
    min_interval_seconds: int = int(os.getenv("ALERT_MIN_INTERVAL_SECONDS", "600"))
    temperature_high_c: float = float(os.getenv("ALERT_TEMPERATURE_HIGH_C", "30"))
    temperature_low_c: float = float(os.getenv("ALERT_TEMPERATURE_LOW_C", "20"))


@dataclass
class AppSettings:
    """Application-wide settings."""

    timezone: str = os.getenv("APP_TIMEZONE", "Asia/Kolkata")


class Settings:
    """Main settings container."""

    mqtt = MQTTSettings()
    database = DatabaseSettings()
    timescale = TimescaleSettings()
    api = APISettings()
    scheduler = SchedulerSettings()
    alerts = AlertSettings()
    app = AppSettings()


    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # FCM (Firebase Cloud Messaging)
    fcm_service_account_json: str = os.getenv("FCM_SERVICE_ACCOUNT_JSON", "tankctl-firebase-adminsdk-fbsvc-2efd3c5518.json")
    fcm_project_id: str = os.getenv("FCM_PROJECT_ID", "")


fcm_service_account_json: str = os.getenv("FCM_SERVICE_ACCOUNT_JSON", "firebase-service-account.json")
fcm_project_id: str = os.getenv("FCM_PROJECT_ID", "")
settings = Settings()
