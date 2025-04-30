from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base

from app.utils.timezone import IST

class EventLog(Base):
    """
    EventLog Model - records major events for each tank.
    """
    __tablename__ = "event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Link the log to a specific tank
    tank_id = Column(UUID(as_uuid=True), ForeignKey("tanks.tank_id"), nullable=False)

    # Event Type: e.g., "registration", "disconnection", "error", "reconnect"
    event_type = Column(String, nullable=False)

    # Optional event description
    description = Column(String, nullable=True)

    # When the event was logged
    timestamp = Column(DateTime, default=datetime.now(IST))

    def __repr__(self):
        return f"<EventLog(tank_id={self.tank_id}, event_type={self.event_type})>"
