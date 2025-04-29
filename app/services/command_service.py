# app/services/command_service.py

from datetime import datetime, timedelta
from app.schemas.command import CommandAcknowledgeRequest
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid

from app.models.tank import Tank
from app.models.tank_command import TankCommand
from app.utils.discord import send_command_acknowledgement_embed
from app.utils.timezone import IST

# Configurable retry policy
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 60  # 1 minute

def issue_command(db: Session, tank_id: uuid.UUID, command_payload: str) -> TankCommand:
    """
    Create a new command for the given tank.
    Allows multiple commands to queue up.
    """
    tank = db.execute(select(Tank).where(Tank.tank_id == tank_id)).scalar_one_or_none()
    if not tank:
        raise ValueError(f"Tank with ID {tank_id} not found")

    new_command = TankCommand(
        tank_id=tank_id,
        command_payload=command_payload,
        status="pending",
        retries=0,
        next_retry_at=datetime.now(IST),
    )
    db.add(new_command)
    db.commit()
    db.refresh(new_command)

    return new_command



def get_pending_command_for_tank(db: Session, tank_id) -> TankCommand | None:
    command = db.execute(
        select(TankCommand)
        .where(
            TankCommand.tank_id == tank_id,
            TankCommand.status.in_(["pending", "in_progress"])
        )
        .order_by(TankCommand.created_at.asc())
    ).scalars().first()  # ✅ FIXED

    return command



def acknowledge_command(db: Session, tank_id: str, ack: CommandAcknowledgeRequest):
    """
    Handle acknowledgment from tank node for command execution.
    """
    command = db.execute(
        select(TankCommand).where(
            TankCommand.command_id == ack.command_id
        )
    ).scalar_one_or_none()  # ✅ safe

    if not command:
        raise ValueError("Command not found.")

    if str(command.tank_id) != str(tank_id):
        raise ValueError("Command does not belong to this tank.")

    command.status = "success" if ack.success else "failed"
    command.retries = 3  # prevent further retries
    command.last_attempt_at = datetime.now(IST)

    db.commit()
    db.refresh(command)

    return {
        "message": f"Command `{command.command_payload}` acknowledged as {'SUCCESS' if ack.success else 'FAILED'}",
        "timestamp": datetime.now(IST).isoformat()
    }



def retry_stale_commands(db: Session):
    """
    Retry pending commands if next_retry_at has passed.
    """
    now = datetime.now(IST)
    stale_commands = db.execute(
        select(TankCommand).where(
            TankCommand.status.in_(["pending", "in_progress"]),
            TankCommand.next_retry_at <= now
        )
    ).scalars().all()

    for command in stale_commands:
        if command.retries >= MAX_RETRIES:
            command.status = "failed"

            # ✅ Properly send a command failure embed
            tank = db.execute(select(Tank).where(Tank.tank_id == command.tank_id)).scalar_one_or_none()
            if tank:
                send_command_acknowledgement_embed(
                    tank_name=tank.tank_name,
                    command_payload=command.command_payload,
                    success=False
                )

        else:
            command.retries += 1
            backoff = BASE_BACKOFF_SECONDS * (2 ** (command.retries - 1))
            command.next_retry_at = now + timedelta(seconds=backoff)

    db.commit()
