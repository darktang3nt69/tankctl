from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime

from app.utils.timezone import IST



class TankAlertState(Base):
    __tablename__ = "tank_alert_state"

    tank_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    last_alert_sent = Column(DateTime, default=datetime.now(IST), nullable=False)
