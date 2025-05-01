from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class TankScheduleLog(Base):
    __tablename__ = "tank_schedule_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tank_id = Column(UUID(as_uuid=True), ForeignKey("tanks.tank_id"), nullable=False)
    event_type = Column(String, nullable=False)  # 'light_on', 'light_off', 'override_cleared'
    trigger_source = Column(String, nullable=False)  # 'manual' or 'scheduled'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    tank = relationship("Tank")
