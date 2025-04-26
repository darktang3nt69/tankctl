"""
Database models for TankCTL.

This module defines all SQLAlchemy models for the application, including:
- Tank management
- Status tracking
- Command handling
- Scheduling
- Event logging

Best Practices:
- Use type hints for better IDE support
- Add comprehensive docstrings
- Define proper relationships
- Use appropriate column types
- Add indexes for performance
- Include timestamps for auditing
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime
from typing import Optional, List, Dict, Any

class Tank(Base):
    """
    Tank model representing an aquarium system.
    
    Attributes:
        id: Unique identifier
        name: Human-readable name
        token: Authentication token
        created_at: Creation timestamp
        last_seen: Last communication timestamp
        is_active: Whether the tank is active
        config: JSON configuration
    """
    __tablename__ = "tanks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    token = Column(String(512), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)
    config = Column(JSON, default={}, nullable=False)
    
    # Relationships
    status_updates = relationship("TankStatus", back_populates="tank", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="tank", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="tank", cascade="all, delete-orphan")
    events = relationship("EventLog", back_populates="tank", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="tank", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="tank", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tank {self.name} (ID: {self.id})>"

class TankStatus(Base):
    """
    Tank status model for tracking sensor readings and system state.
    
    Attributes:
        id: Unique identifier
        tank_id: Foreign key to Tank
        timestamp: Status update timestamp
        status: JSON status data
    """
    __tablename__ = "tank_status"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(JSON, nullable=False)
    
    # Relationships
    tank = relationship("Tank", back_populates="status_updates")
    
    # Indexes
    __table_args__ = (
        Index('ix_tank_status_tank_timestamp', 'tank_id', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<TankStatus {self.id} for Tank {self.tank_id}>"

class Command(Base):
    """
    Command model for managing tank control commands.
    
    Attributes:
        id: Unique identifier
        tank_id: Foreign key to Tank
        command: Command type
        parameters: Command parameters
        created_at: Command creation timestamp
        acknowledged: Whether command was acknowledged
        ack_time: Acknowledgment timestamp
        retry_count: Number of retry attempts
    """
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    command = Column(String(50), nullable=False)
    parameters = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged = Column(Boolean, default=False, nullable=False)
    ack_time = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    tank = relationship("Tank", back_populates="commands")
    
    # Indexes
    __table_args__ = (
        Index('ix_commands_tank_acknowledged', 'tank_id', 'acknowledged'),
    )

    def __repr__(self) -> str:
        return f"<Command {self.id} for Tank {self.tank_id}>"

class Schedule(Base):
    """
    Schedule model for managing recurring tank actions.
    
    Attributes:
        id: Unique identifier
        tank_id: Foreign key to Tank
        action: Action type
        time: Scheduled time
        days: Days of week (0-6)
        is_active: Whether schedule is active
    """
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)
    time = Column(String(5), nullable=False)  # Format: "HH:MM"
    days = Column(JSON, nullable=False)  # List of days [0-6]
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tank = relationship("Tank", back_populates="schedules")
    
    # Indexes
    __table_args__ = (
        Index('ix_schedules_tank_action', 'tank_id', 'action'),
    )

    def __repr__(self) -> str:
        return f"<Schedule {self.id} for Tank {self.tank_id}>"

class EventLog(Base):
    """
    Event log model for tracking system events.
    
    Attributes:
        id: Unique identifier
        tank_id: Foreign key to Tank
        event_type: Type of event
        details: Event details
        timestamp: Event timestamp
    """
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    details = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    tank = relationship("Tank", back_populates="events")
    
    # Indexes
    __table_args__ = (
        Index('ix_event_logs_tank_timestamp', 'tank_id', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<EventLog {self.id} for Tank {self.tank_id}>"

class Metric(Base):
    """
    Metric model for tracking tank measurements and statistics.
    
    Attributes:
        id: Unique identifier
        tank_id: Foreign key to Tank
        name: Metric name (e.g., temperature, ph_level)
        value: Metric value
        timestamp: Measurement timestamp
    """
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    value = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    tank = relationship("Tank", back_populates="metrics")
    
    # Indexes
    __table_args__ = (
        Index('ix_metrics_tank_name_timestamp', 'tank_id', 'name', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<Metric {self.name}={self.value} for Tank {self.tank_id}>"

class Alert(Base):
    """
    Alert model for tracking system alerts and notifications.
    
    Attributes:
        id: Unique identifier
        tank_id: Foreign key to Tank
        alert_type: Type of alert
        message: Alert message
        severity: Alert severity level
        created_at: Alert creation timestamp
        resolved: Whether alert is resolved
        resolved_at: Resolution timestamp
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(Integer, ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    message = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    tank = relationship("Tank", back_populates="alerts")
    
    # Indexes
    __table_args__ = (
        Index('ix_alerts_tank_created', 'tank_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Alert {self.alert_type} for Tank {self.tank_id}>" 