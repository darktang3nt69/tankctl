from sqlalchemy.orm import Session
from app.models.tank_audit_log import TankAuditLog
from datetime import datetime

def log_tank_event(db: Session, tank_id: str, event_type: str, details: dict = None):
    audit_entry = TankAuditLog(
        tank_id=tank_id,
        event_type=event_type,
        event_time=datetime.utcnow(),
        details=details
    )
    db.add(audit_entry)
    db.commit()
