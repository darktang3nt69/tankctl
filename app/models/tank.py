from sqlalchemy import Column, String, DateTime, Boolean, Float, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base

class Tank(Base):
    """
    Tank Model - represents a physical tank device.
    """
    __tablename__ = "tanks"
    __table_args__ = {'extend_existing': True}


    tank_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tank_name = Column(String, unique=True, nullable=False)
    location = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)

    last_seen = Column(DateTime(timezone=True), default=func.now())
    is_online = Column(Boolean, default=True)

    token = Column(String, nullable=True)

    temperature = Column(Float, nullable=True)
    ph = Column(Float, nullable=True)
    light_state = Column(Boolean, nullable=True)

    def __repr__(self):
        return f"<Tank(tank_id={self.tank_id}, is_online={self.is_online})>"
