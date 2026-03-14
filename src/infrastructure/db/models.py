"""
SQLAlchemy database models for TankCtl.

These models map to PostgreSQL and TimescaleDB tables.
"""

from datetime import datetime
import json

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Time, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DeviceModel(Base):
    """Device table model."""

    __tablename__ = "devices"

    device_id = Column(String(50), primary_key=True)
    device_secret = Column(String(100), nullable=False)
    status = Column(String(20), default="offline")
    firmware_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    uptime_ms = Column(Integer, nullable=True)
    rssi = Column(Integer, nullable=True)
    wifi_status = Column(String(50), nullable=True)
    temp_threshold_low = Column(Float, nullable=True)
    temp_threshold_high = Column(Float, nullable=True)
    device_name = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    icon_type = Column(String(50), default="fish_bowl")
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<DeviceModel(device_id={self.device_id}, status={self.status})>"


class DeviceShadowModel(Base):
    """Device shadow state table model."""

    __tablename__ = "device_shadows"

    device_id = Column(String(50), primary_key=True)
    desired = Column(Text, default="{}")  # JSON string
    reported = Column(Text, default="{}")  # JSON string
    version = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DeviceShadowModel(device_id={self.device_id}, version={self.version})>"


class CommandModel(Base):
    """Command table model."""

    __tablename__ = "commands"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), nullable=False)
    command = Column(String(100), nullable=False)
    value = Column(String(250), nullable=True)
    version = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<CommandModel(id={self.id}, device_id={self.device_id}, command={self.command})>"


class TelemetryModel(Base):
    """Telemetry table model for TimescaleDB."""

    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    additional_metadata = Column(Text, nullable=True)  # JSON string for additional data

    def __repr__(self):
        return f"<TelemetryModel(device_id={self.device_id}, metric={self.metric_name})>"


class EventRecord(Base):
    """Event record table model for audit trail and observability."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event = Column(String(100), nullable=False, index=True)
    device_id = Column(String(100), nullable=True, index=True)
    timestamp = Column(Float, nullable=False, index=True)
    event_metadata = Column("metadata", Text, nullable=True)  # JSON string - mapped to 'metadata' column
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<EventRecord(id={self.id}, event={self.event}, device_id={self.device_id})>"
    
    def to_domain(self):
        """Convert database record to domain event."""
        from src.domain.event import Event
        
        metadata = {}
        if self.event_metadata:
            try:
                metadata = json.loads(self.event_metadata)
            except json.JSONDecodeError:
                metadata = {}
        
        return Event(
            event=self.event,
            timestamp=self.timestamp,
            device_id=self.device_id,
            metadata=metadata,
        )


class LightScheduleModel(Base):
    """Light schedule table model for automated lighting control."""

    __tablename__ = "light_schedules"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), nullable=False, unique=True)
    enabled = Column(Boolean, default=True, nullable=False)
        start_time = Column(Time, nullable=False)
        end_time = Column(Time, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LightScheduleModel(device_id={self.device_id}, start={self.start_time}, end={self.end_time}, enabled={self.enabled})>"


class WaterScheduleModel(Base):
    """Water change reminder schedule table model."""

    __tablename__ = "water_schedules"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), nullable=False, index=True)
    schedule_type = Column(String(20), nullable=False)  # 'weekly' or 'custom'
    day_of_week = Column(Integer, nullable=True)  # 0-6 for weekly
    schedule_date = Column(String(10), nullable=True)  # YYYY-MM-DD for custom
    schedule_time = Column(Time, nullable=False)
    notes = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<WaterScheduleModel(device_id={self.device_id}, type={self.schedule_type})>"


class WarningAcknowledgementModel(Base):
    """Stores acknowledged warning codes per device."""

    __tablename__ = "warning_acknowledgements"
    __table_args__ = (
        UniqueConstraint("device_id", "warning_code", name="uq_warning_ack_device_code"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(100), nullable=False, index=True)
    warning_code = Column(String(100), nullable=False, index=True)
    acknowledged_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            "<WarningAcknowledgementModel("
            f"device_id={self.device_id}, warning_code={self.warning_code}"
            ")>"
        )


class DevicePushTokenModel(Base):
    """Device push token table model for FCM, etc."""
    __tablename__ = "device_push_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, nullable=False, index=True)
    token = Column(String, nullable=False, unique=True)
    platform = Column(String, nullable=False)  # e.g., 'android', 'ios'
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<DevicePushToken(device_id={self.device_id}, platform={self.platform}, last_seen={self.last_seen})>"
        )
