from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base

class TankCommand(Base):
    """
    Tank Command Model - represents a command issued to a tank.
    """
    __tablename__ = "tank_commands"
    __table_args__ = {'extend_existing': True}

    command_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tank_id = Column(UUID(as_uuid=True), ForeignKey("tanks.tank_id"), nullable=False)

    command_payload = Column(String, nullable=False)  # e.g., "feed_now", "light_on"
    status = Column(String, default="pending")         # pending, acknowledged, failed
    retries = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    tank = relationship("Tank", back_populates="tank_commands")