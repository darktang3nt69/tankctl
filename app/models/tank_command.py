# app/models/tank_command.py

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import IST
from datetime import datetime
import uuid

class TankCommand(Base):
    __tablename__ = "tank_commands"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    tank_id = Column(String, ForeignKey("tanks.tank_id"), nullable=False)

    command = Column(String, nullable=False)  # Only: feed_now, light_on, light_off (future extendable)
    status = Column(String, default="queued")  # queued, acknowledged, success, failed
    retries = Column(Integer, default=0)

    last_attempt = Column(DateTime(timezone=True), default=lambda: datetime.now(IST))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(IST))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(IST))

    tank = relationship("Tank", back_populates="commands")
