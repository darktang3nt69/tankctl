# app/services/command_service.py

from datetime import datetime, timedelta
from app.schemas.command import CommandAcknowledgeRequest
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import uuid
import os
from typing import Any, Dict, List, Tuple

from app.models.tank import Tank
from app.models.tank_command import TankCommand
from app.models.tank_settings import TankSettings
from app.models.tank_schedule_log import TankScheduleLog
from app.utils.discord import send_discord_embed
from app.utils.timezone import IST

# Configurable retry policy for commands.
# MAX_RETRIES: Maximum number of times a command will be retried before being marked as 'failed'.
# BASE_BACKOFF_SECONDS: The initial delay for retries. Subsequent retries use exponential backoff.
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
BASE_BACKOFF_SECONDS = int(os.getenv("BASE_BACKOFF_SECONDS", 60))

def issue_command(
    db: Session,
    tank_id: uuid.UUID,
    command_type: str,
    parameters: Dict[str, Any] = {},
    source: str = "system"
) -> TankCommand:
    """
    Centralized function to create commands for tanks.
    Supports both manual (admin-initiated) and system (scheduled) command creation.

    Business Logic:
    - Ensures the target tank exists before issuing a command.
    - For 'manual' source commands, it updates the tank's `manual_override_state`
      if the command is 'light_on' or 'light_off'. This is a direct override
      of the scheduled lighting.
    - Records the command in the `tank_commands` table with a 'pending' status.
    - Sets the `next_retry_at` to the current time, making it immediately eligible for processing.
    - Logs manual and scheduled commands in `tank_schedule_log` for historical tracking.
    """
    # Retrieve the tank from the database.
    tank = db.execute(select(Tank).where(Tank.tank_id == tank_id)).scalar_one_or_none()
    if not tank:
        raise ValueError(f"Tank with ID {tank_id} not found")

    # Construct the command_payload as a JSONB object
    command_payload = {"command_type": command_type, "parameters": parameters}

    # If the command is from a 'manual' source (admin override) and settings exist,
    # update the manual override state for lights. This ensures the system respects
    # immediate human intervention over automated schedules.
    settings = db.execute(select(TankSettings).where(TankSettings.tank_id == tank_id)).scalar_one_or_none()
    if source == "manual" and command_type in ["light_on", "light_off"] and settings:
        if command_type == "light_on":
            settings.manual_override_state = "on"
            send_discord_embed(status="manual_light_on", tank_name=tank.tank_name, command_payload=command_type)
        elif command_type == "light_off":
            settings.manual_override_state = "off"
            send_discord_embed(status="manual_light_off", tank_name=tank.tank_name, command_payload=command_type)

    # Create a new TankCommand entry.
    new_command = TankCommand(
        tank_id=tank_id,
        command_payload=command_payload, # Store as JSONB
        status="pending",
        retries=0,
        next_retry_at=datetime.now(IST),
    )
    db.add(new_command)

    # Log the command in the tank_schedule_log table if it's a manual or scheduled event.
    # This provides an audit trail for important commands.
    if source in ["manual", "scheduled"]:
        db.add(TankScheduleLog(
            tank_id=tank_id,
            event_type=command_type, # Log command_type here
            trigger_source=source
        ))

    db.commit()
    db.refresh(new_command)

    return new_command

def get_command_by_id(db: Session, command_id: uuid.UUID) -> TankCommand | None:
    """
    Retrieves a command by its ID.
    """
    return db.scalars(select(TankCommand).where(TankCommand.command_id == command_id)).first()

def get_pending_command_for_tank(db: Session, tank_id: uuid.UUID) -> TankCommand | None:
    """
    Retrieves the oldest pending or in-progress command for a specific tank.
    Commands are ordered by creation time to ensure FIFO processing.
    """
    command = db.execute(
        select(TankCommand)
        .where(
            TankCommand.tank_id == tank_id,
            TankCommand.status.in_(["pending", "in_progress"])
        )
        .order_by(TankCommand.created_at.asc())
    ).scalars().first()

    return command

def acknowledge_command(db: Session, tank_id: uuid.UUID, ack: CommandAcknowledgeRequest):
    """
    Handles the acknowledgment of a command execution from a tank node.

    Business Logic:
    - Fetches the command by its `command_id`.
    - Verifies that the command belongs to the acknowledging tank (`tank_id`).
    - Updates the command's status to 'success' or 'failed' based on `ack.success`.
    - Sets `retries` to `MAX_RETRIES` (3) to prevent further retries for acknowledged commands.
    - Records the `last_attempt_at` timestamp.
    - Triggers a Discord notification to inform about the command acknowledgment status.
    """
    # Fetch the command to be acknowledged.
    command = db.execute(
        select(TankCommand).where(
            TankCommand.command_id == ack.command_id
        )
    ).scalar_one_or_none()

    if not command:
        raise ValueError("Command not found.")

    # Ensure the command belongs to the tank acknowledging it for security and data integrity.
    if command.tank_id != tank_id:
        raise ValueError("Command does not belong to this tank.")

    # Update the command status based on the acknowledgment result.
    command.status = "success" if ack.success else "failed"
    command.retries = MAX_RETRIES  # Prevent further retries after acknowledgment.
    command.last_attempt_at = datetime.now(IST)
    command.completed_at = datetime.now(IST) # Set completion time
    command.result = "Command executed successfully" if ack.success else "Command execution failed" # Set result

    db.commit()
    db.refresh(command)

    # Prepare and send a Discord notification about the command acknowledgment.
    # This provides real-time feedback on tank operations.
    tank = db.query(Tank).filter(Tank.tank_id == tank_id).first()
    if tank and command:
        send_discord_embed(
            status="command_ack",
            tank_name=tank.tank_name,
            command_payload=command.command_payload.get("command_type", "unknown"), # Use command_type from payload
            success=ack.success,
            extra_fields={
                "Command ID": str(command.command_id),
                "Status": command.status.capitalize(),
                "Acknowledged At": datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z%z')
            }
        )

def get_commands(
    db: Session,
    tank_id: uuid.UUID | None = None,
    status: str | None = None,
    command_type: str | None = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[TankCommand], int]:
    """
    Retrieves a list of commands with optional filters and pagination.
    Returns a tuple of (commands, total_count).
    """
    query = select(TankCommand)

    if tank_id:
        query = query.where(TankCommand.tank_id == tank_id)
    if status:
        query = query.where(TankCommand.status == status)
    if command_type:
        query = query.where(TankCommand.command_payload["command_type"].astext == command_type)

    total_count = db.scalar(select(func.count()).select_from(query.subquery()))

    query = query.order_by(TankCommand.created_at.desc()).offset(skip).limit(limit)
    commands = db.scalars(query).all()

    return commands, total_count

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

    Business Logic:
    - Filters commands by `tank_id`.
    - Supports optional filtering by `status`, `start_time`, and `end_time`.
    - Orders results by `created_at` in descending order (most recent first).
    - Limits the number of returned results to `limit`.
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

    return commands

def retry_stale_commands(db: Session):
    """
    Identifies and retries commands that are 'pending' or 'in_progress' and have
    exceeded their `next_retry_at` timestamp. Commands are retried with an
    exponential backoff policy.

    Business Logic:
    - Selects the oldest eligible command for each tank that is due for a retry.
    - If a command has reached `MAX_RETRIES`, it is marked as 'failed' and a Discord
      notification is sent.
    - Otherwise, the command's `retries` count is incremented, `next_retry_at` is
      calculated using exponential backoff, status is set to 'delivered', and a
      Discord notification is sent.
    - All changes are persisted to the database.
    """
    now = datetime.now(IST)

    # 1) Identify head-of-line per tank: Find the single oldest pending/in_progress
    # command for each tank that has passed its next_retry_at time.
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

    # 2) Fetch those full command rows by joining with the subquery results.
    head_cmds = (
        db.query(TankCommand)
          .join(
             subq,
             (TankCommand.tank_id == subq.c.tank_id) &
             (TankCommand.created_at == subq.c.min_created)
          )
          .all()
    )

    print(f"📦 Head-of-line commands eligible for retry: {len(head_cmds)}")

    failed, retried = 0, 0

    for command in head_cmds:
        tank = db.get(Tank, command.tank_id)
        tank_name = tank.tank_name if tank else "<unknown>"

        # If the command has exhausted its allowed retries, mark it as permanently failed.
        if command.retries >= MAX_RETRIES:
            failed += 1
            command.status = "failed"
            command.completed_at = now # Set completion time for failed commands
            command.result = "Command failed after multiple retries" # Set result
            print(f"❌ Command {command.command_id} FAILED for tank {tank_name} after {command.retries} retries.")
            send_discord_embed(
                status="retry_failed",
                tank_name=tank_name,
                command_payload=command.command_payload.get("command_type", "unknown"),
                extra_fields={
                    "Retries": str(command.retries),
                    "Status": "Permanently failed"
                }
            )
        else:
            # Otherwise, increment retry count and schedule the next retry with exponential backoff.
            command.retries += 1
            backoff = BASE_BACKOFF_SECONDS * (2 ** (command.retries - 1))
            command.next_retry_at = now + timedelta(seconds=backoff)
            command.status = "delivered" # Set status to 'delivered' when retrying
            retried += 1

            print(f"🔁 Retrying command {command.command_id} for tank {tank_name} | "
                  f"Retry #{command.retries} | Next retry at {command.next_retry_at.strftime('%H:%M:%S')}")
            send_discord_embed(
                status="retry_scheduled",
                tank_name=tank_name,
                extra_fields={
                    "Command":       command.command_payload.get("command_type", "unknown"),
                    "Retry #":       str(command.retries),
                    "Next Retry At": command.next_retry_at.strftime('%d %b %Y %I:%M %p IST')
                }
            )

        # Persist the updated state of the command to the database.
        db.add(command)

    db.commit()

    print("-" * 80)
    print(f"🔁 Commands retried: {retried} | ❌ Permanently failed: {failed}")
    print("=" * 80)