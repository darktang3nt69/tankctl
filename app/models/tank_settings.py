from sqlalchemy import Column, ForeignKey, Time, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class TankSettings(Base):
    __tablename__ = "tank_settings"
    __table_args__ = {'extend_existing': True}


    tank_id = Column(UUID(as_uuid=True), ForeignKey("tanks.tank_id"), primary_key=True)
    
    # Lighting schedule
    light_on = Column(Time(timezone=True), nullable=True)
    light_off = Column(Time(timezone=True), nullable=True)

    # Manual override: 'on', 'off', or None
    manual_override_state = Column(String, nullable=True)  # 'on', 'off', or null

    # To prevent duplicate triggers
    last_schedule_check_on = Column(DateTime(timezone=True), nullable=True)
    last_schedule_check_off = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tank = relationship("Tank", back_populates="settings")
