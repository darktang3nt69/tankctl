# app/models/tank_settings.py

import uuid
from datetime import time
from sqlalchemy import (
    Column,
    ForeignKey,
    Time,
    DateTime,
    Boolean,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class TankSettings(Base):
    __tablename__ = "tank_settings"
    __table_args__ = {"extend_existing": True}

    # 1:1 primary key → Tank.tank_id
    tank_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tanks.tank_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Lighting schedule with defaults 10:00 → 16:00
    light_on = Column(
        Time(timezone=True),
        nullable=False,
        default=lambda: time(hour=10, minute=0),
    )
    light_off = Column(
        Time(timezone=True),
        nullable=False,
        default=lambda: time(hour=16, minute=0),
    )

    # Enable/disable scheduler
    is_schedule_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Manual override: 'on', 'off', or NULL
    manual_override_state = Column(
        String,
        nullable=True,
    )

    # Prevent duplicate triggers within same window
    last_schedule_check_on = Column(DateTime(timezone=True), nullable=True)
    last_schedule_check_off = Column(DateTime(timezone=True), nullable=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Back‐reference to Tank
    tank = relationship("Tank", back_populates="settings")
