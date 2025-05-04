from sqlalchemy.orm import Session
import uuid

from app.models.tank_command import TankCommand

from app.services.command_service import issue_command

def issue_admin_command(db: Session, tank_id: uuid.UUID, command_payload: str) -> TankCommand:
    return issue_command(db, tank_id, command_payload, source="manual")