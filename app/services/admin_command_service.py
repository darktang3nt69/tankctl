# app/services/admin_command_service.py

import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.tank import Tank
from app.models.tank_command import TankCommand
from app.utils.timezone import IST

def issue_admin_command(db: Session, tank_id: uuid.UUID, command_payload: str) -> TankCommand:
    tank = db.query(Tank).filter(Tank.tank_id == tank_id).first()
    if not tank:
        raise ValueError("Tank not found")

    command = TankCommand(
        command_id=uuid.uuid4(),
        tank_id=tank.tank_id,
        command_payload=command_payload,
        status="pending",
        retries=0,
        next_retry_at=datetime.now(IST) + timedelta(minutes=1),
        created_at=datetime.now(IST)
    )
    db.add(command)
    db.commit()
    db.refresh(command)
    return command
