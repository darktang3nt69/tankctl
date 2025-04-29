from sqlalchemy import Column, String, DateTime, JSON, Integer
from core.database import Base
import uuid

class TankAuditLog(Base):
    __tablename__ = "tank_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    tank_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    event_time = Column(DateTime, nullable=False)
    details = Column(JSON)
