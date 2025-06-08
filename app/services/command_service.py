# app/services/command_service.py

from datetime import datetime, timedelta
from app.schemas.command import CommandAcknowledgeRequest
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import uuid
import os

from app.models.tank import Tank
from app.models.tank_command import TankCommand
from app.models.tank_settings import TankSettings
from app.models.tank_schedule_log import TankScheduleLog
from app.utils.discord import send_discord_embed
from app.utils.timezone import IST

# Configurable retry policy
MAX_RETRIES = os.getenv("", 3)
BASE_BACKOFF_SECONDS = 60  # 1 minute

def issue_command(
    db: Session,
    tank_id: uuid.UUID,
    command_payload: str,
    source: str = "system"
) -> TankCommand:
    """
    Centralized function to create commands for tanks.
    Supports both manual and scheduled creation.
    """
    tank = db.execute(select(Tank).where(Tank.tank_id == tank_id)).scalar_one_or_none()
    if not tank:
        raise ValueError(f"Tank with ID {tank_id} not found")

    # Check for and update tank settings if override is needed
    settings = db.execute(select(TankSettings).where(TankSettings.tank_id == tank_id)).scalar_one_or_none()
    if source == "manual" and settings:
        if command_payload == "light_on":
            settings.manual_override_state = "on"
        elif command_payload == "light_off":
            settings.manual_override_state = "off"

    # Create command entry
    new_command = TankCommand(
        tank_id=tank_id,
        command_payload=command_payload,
        status="pending",
        retries=0,
        next_retry_at=datetime.now(IST),
    )
    db.add(new_command)

    # Log the command
    if source in ["manual", "scheduled"]:
        db.add(TankScheduleLog(
            tank_id=tank_id,
            event_type=command_payload,
            trigger_source=source
        ))

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

def get_command_history_for_tank(
    db: Session,
    tank_id: uuid.UUID,
    status: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100
) -> list[TankCommand]:
    """
    Retrieve command history for a specific tank, with optional filters.
    """
    query = select(TankCommand).where(TankCommand.tank_id == tank_id)

    if status:
        query = query.where(TankCommand.status == status)
    if start_time:
        query = query.where(TankCommand.created_at >= start_time)
    if end_time:
        query = query.where(TankCommand.created_at <= end_time)

    query = query.order_by(TankCommand.created_at.desc()).limit(limit)
    commands = db.scalars(query).all()

    for command in commands:
        print(f"DEBUG: Command ID: {command.command_id}, created_at.tzinfo: {command.created_at.tzinfo}, next_retry_at.tzinfo: {command.next_retry_at.tzinfo if command.next_retry_at else 'None'}")

    return commands

def retry_stale_commands(db: Session):
    """
    Retry exactly one command per tank: find the oldest pending/in_progress
    whose next_retry_at <= now, then retry or mark failed.
    """
    now = datetime.now(IST)

    # 1) Identify head‐of‐line per tank
    subq = (
        db.query(
            TankCommand.tank_id,
            func.min(TankCommand.created_at).label("min_created")
        )
        .filter(
            TankCommand.status.in_(["pending", "in_progress"]),
            TankCommand.next_retry_at <= now
        )
        .group_by(TankCommand.tank_id)
        .subquery()
    )

    # 2) Fetch those full command rows
    head_cmds = (
        db.query(TankCommand)
          .join(
             subq,
             (TankCommand.tank_id == subq.c.tank_id) &
             (TankCommand.created_at == subq.c.min_created)
          )
          .all()
    )

    print(f"📦 Head‐of‐line commands eligible for retry: {len(head_cmds)}")

    failed, retried = 0, 0

    for command in head_cmds:
        tank = db.get(Tank, command.tank_id)
        tank_name = tank.tank_name if tank else "<unknown>"

        # If it's already hit max retries → mark failed
        if command.retries >= MAX_RETRIES:
            failed += 1
            command.status = "failed"
            print(f"❌ Command {command.command_id} FAILED for tank {tank_name} after {command.retries} retries.")
            send_discord_embed(
                status="retry_failed",
                tank_name=tank_name,
                command_payload=command.command_payload,
                extra_fields={
                    "Retries": str(command.retries),
                    "Status": "Permanently failed"
                }
            )
        else:
            # Otherwise increment attempts, schedule next retry, and fire it
            command.retries += 1
            backoff = BASE_BACKOFF_SECONDS * (2 ** (command.retries - 1))
            command.next_retry_at = now + timedelta(seconds=backoff)
            command.status = "delivered"
            retried += 1

            print(f"🔁 Retrying command {command.command_id} for tank {tank_name} | "
                  f"Retry #{command.retries} | Next retry at {command.next_retry_at.strftime('%H:%M:%S')}")
            send_discord_embed(
                status="retry_scheduled",
                tank_name=tank_name,
                extra_fields={
                    "Command":       command.command_payload,
                    "Retry #":       str(command.retries),
                    "Next Retry At": command.next_retry_at.strftime('%d %b %Y %I:%M %p IST')
                }
            )

        # persist this command's updated state
        db.add(command)

    db.commit()

    print("-" * 80)
    print(f"🔁 Commands retried: {retried} | ❌ Permanently failed: {failed}")
    print("=" * 80)