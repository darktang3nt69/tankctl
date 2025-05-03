from sqlalchemy import Column, Float, Boolean, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base

from app.utils.timezone import IST


import uuid

class StatusLog(Base):
    """
    StatusLog Model - stores regular status updates from tanks.
    """
    __tablename__ = "status_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Link to the tank sending this status update
    tank_id = Column(UUID(as_uuid=True), ForeignKey("tanks.tank_id"), nullable=False)

    # Measurements from the tank
    temperature = Column(Float, nullable=True)  # In degrees Celsius
    ph = Column(Float, nullable=True)           # pH level
    light_state = Column(Boolean, nullable=True)  # Whether tank light is ON or OFF
    firmware_version = Column(String, nullable=True)  # Version of firmware running

    # When the status update was sent
    timestamp = Column(DateTime, default=datetime.now(IST))

    def __repr__(self):
        return f"<StatusLog(tank_id={self.tank_id}, temperature={self.temperature}, ph={self.ph})>"
