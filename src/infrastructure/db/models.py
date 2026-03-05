"""
SQLAlchemy database models for TankCtl.

These models map to PostgreSQL and TimescaleDB tables.
"""

from datetime import datetime
import json

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
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
    metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<EventRecord(id={self.id}, event={self.event}, device_id={self.device_id})>"
    
    def to_domain(self):
        """Convert database record to domain event."""
        from src.domain.event import Event
        
        metadata = {}
        if self.metadata:
            try:
                metadata = json.loads(self.metadata)
            except json.JSONDecodeError:
                metadata = {}
        
        return Event(
            event=self.event,
            timestamp=self.timestamp,
            device_id=self.device_id,
            metadata=metadata,
        )
