"""
Command tasks for TankCTL.

This module contains Celery tasks for handling tank commands with retry logic.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
from celery import shared_task
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Command, EventLog, CommandStatus
from app.tasks.notifications import send_discord_notification
from app.core.celery import celery_app
from app.core.metrics import command_counter, command_queue_size, node_health
import logging

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    max_retries=5,  # Increased from 3 to 5
    default_retry_delay=60,  # 1 minute base delay
    queue="commands",
    time_limit=300,  # 5 minutes
    soft_time_limit=240,  # 4 minutes
    acks_late=True,
    reject_on_worker_lost=True
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
            logger.error(f"Command {command_id} not found")
            raise ValueError(f"Command {command_id} not found")
        
        # Update command status to in progress
        command.status = CommandStatus.IN_PROGRESS
        command.last_retry = datetime.now(UTC)
        db.commit()
        
        # Check if command has timed out
        if command.created_at + timedelta(seconds=command.timeout) < datetime.now(UTC):
            command.status = CommandStatus.TIMED_OUT
            command.error_message = "Command timed out"
            db.commit()
            
            # Log timeout event
            event = EventLog(
                tank_id=command.tank_id,
                event_type="command_timeout",
                details={
                    "command_id": command.id,
                    "command": command.command,
                    "timeout": command.timeout
                }
            )
            db.add(event)
            db.commit()
            
            # Update metrics and notify
            command_counter.labels(
                tank_id=str(command.tank_id),
                command=command.command,
                status="timeout"
            ).inc()
            
            send_discord_notification.delay(
                f"⏰ Command {command.command} for tank {command.tank_id} timed out after {command.timeout} seconds"
            )
            return
        
        # Check if command was acknowledged
        if command.acknowledged:
            command.status = CommandStatus.COMPLETED
            db.commit()
            
            # Update metrics
            command_counter.labels(
                tank_id=str(command.tank_id),
                command=command.command,
                status="completed"
            ).inc()
            return
        
        # If command is not acknowledged and retry count is max, mark as failed
        if command.retry_count >= self.max_retries:
            command.status = CommandStatus.FAILED
            command.error_message = f"Failed after {self.max_retries} retries"
            db.commit()
            
            # Log failure event
            event = EventLog(
                tank_id=command.tank_id,
                event_type="command_failed",
                details={
                    "command_id": command.id,
                    "command": command.command,
                    "retry_count": command.retry_count,
                    "error": command.error_message
                }
            )
            db.add(event)
            db.commit()
            
            # Update metrics
            command_counter.labels(
                tank_id=str(command.tank_id),
                command=command.command,
                status="failed"
            ).inc()
            
            # Send Discord notification
            send_discord_notification.delay(
                f"❌ Command {command.command} for tank {command.tank_id} failed after {command.retry_count} retries"
            )
            return
        
        # Increment retry count and schedule retry
        command.retry_count += 1
        command.last_retry = datetime.now(UTC)
        db.commit()
        
        # Update metrics
        command_counter.labels(
            tank_id=str(command.tank_id),
            command=command.command,
            status="retry"
        ).inc()
        
        # Schedule next retry with exponential backoff (1m, 2m, 4m, 8m, 16m)
        next_retry = 60 * (2 ** (command.retry_count - 1))
        logger.info(f"Scheduling retry {command.retry_count} for command {command_id} in {next_retry} seconds")
        self.retry(countdown=next_retry)
        
    except Exception as exc:
        logger.error(f"Error processing command {command_id}: {str(exc)}")
        if command:
            command.error_message = str(exc)
            db.commit()
        self.retry(exc=exc)
    finally:
        db.close()

@celery_app.task(queue="commands")
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
            status=CommandStatus.PENDING,
            acknowledged=False
        )
        db.add(new_command)
        db.commit()
        db.refresh(new_command)
        
        # Update metrics
        command_queue_size.labels(tank_id=str(tank_id)).inc()
        command_counter.labels(
            tank_id=str(tank_id),
            command=command,
            status="queued"
        ).inc()
        
        # Start processing the command
        process_command.delay(new_command.id)
        
        return new_command.id
    finally:
        db.close() 

@celery_app.task(queue="commands")
def update_node_health(tank_id: int, is_healthy: bool) -> None:
    """Update the health status of a tank node."""
    node_health.labels(tank_id=str(tank_id)).set(1 if is_healthy else 0) 