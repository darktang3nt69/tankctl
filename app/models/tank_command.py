from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.utils.timezone import IST
import uuid
from datetime import datetime

from app.core.database import Base

class TankCommand(Base):
    """
    Tank Command Model - represents a command issued to a tank.
    """
    __tablename__ = "tank_commands"
    __table_args__ = {'extend_existing': True}

    command_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tank_id = Column(UUID(as_uuid=True), ForeignKey("tanks.tank_id"), nullable=False)

    command_payload = Column(JSONB, nullable=False)  # e.g., {"command_type": "feed_now", "parameters": {}}
    status = Column(String, default="pending")         # pending, acknowledged, failed
    retries = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(IST), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST), nullable=False)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    tank = relationship("Tank", back_populates="tank_commands")