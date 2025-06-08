from datetime import time, datetime
from sqlalchemy import (
    Column,
    ForeignKey,
    Time,
    DateTime,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import IST

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

    # Pause scheduling until this timestamp (one‐shot override)
    schedule_paused_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Skip scheduling until this timestamp",
    )

    # Prevent duplicate triggers within same window
    last_schedule_check_on = Column(DateTime(timezone=True), nullable=True)
    last_schedule_check_off = Column(DateTime(timezone=True), nullable=True)

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(IST),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(IST),
        onupdate=lambda: datetime.now(IST),
        nullable=False,
    )

    # Back‐reference to Tank
    tank = relationship("Tank", back_populates="settings")
