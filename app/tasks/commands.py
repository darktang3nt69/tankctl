"""
Command tasks for TankCTL.

This module contains Celery tasks for handling tank commands with retry logic.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
from celery import shared_task
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Command, EventLog
from app.tasks.notifications import send_discord_notification

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    queue="commands"
)
def process_command(self, command_id: int) -> None:
    """
    Process a tank command with retry logic.
    
    Args:
        command_id: The ID of the command to process
    """
    db: Session = next(get_db())
    try:
        command = db.query(Command).filter(Command.id == command_id).first()
        if not command:
            raise ValueError(f"Command {command_id} not found")
        
        # Check if command was acknowledged
        if command.acknowledged:
            return
        
        # If command is not acknowledged and retry count is max, mark as failed
        if command.retry_count >= 3:
            # Log failure event
            event = EventLog(
                tank_id=command.tank_id,
                event_type="command_failed",
                details={
                    "command_id": command.id,
                    "command": command.command,
                    "retry_count": command.retry_count
                }
            )
            db.add(event)
            db.commit()
            
            # Send Discord notification
            send_discord_notification.delay(
                f"Command {command.command} for tank {command.tank_id} failed after 3 retries"
            )
            return
        
        # Increment retry count
        command.retry_count += 1
        db.commit()
        
        # Schedule next retry with exponential backoff
        next_retry = 60 * (2 ** (command.retry_count - 1))  # 1m, 2m, 4m
        self.retry(countdown=next_retry)
        
    except Exception as exc:
        self.retry(exc=exc)
    finally:
        db.close()

@shared_task
def schedule_command(tank_id: int, command: str, parameters: dict = None) -> int:
    """Schedule a command for a tank."""
    db = next(get_db())
    try:
        # Create new command
        new_command = Command(
            tank_id=tank_id,
            command=command,
            parameters=parameters,
            created_at=datetime.now(UTC),
            acknowledged=False
        )
        db.add(new_command)
        db.commit()
        db.refresh(new_command)
        return new_command.id
    finally:
        db.close() 