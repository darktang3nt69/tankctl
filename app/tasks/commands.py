"""
Command tasks for TankCTL.

This module contains Celery tasks for handling tank commands with retry logic.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
from celery import shared_task
from sqlalchemy.orm import Session
from app.db.session import get_sync_db
from app.db.models import Command, EventLog, CommandStatus, Tank
from app.tasks.notifications import send_discord_notification
from app.core.celery import celery_app
from app.core.metrics import command_counter, command_queue_size, node_health
import logging
import time

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
    """Process a command for a tank."""
    db = next(get_sync_db())
    try:
        command = db.query(Command).filter(Command.id == command_id).first()
        if not command:
            logger.error(f"Command {command_id} not found")
            return

        tank = db.query(Tank).filter(Tank.id == command.tank_id).first()
        if not tank:
            logger.error(f"Tank {command.tank_id} not found")
            return

        # Update command status
        command.status = CommandStatus.IN_PROGRESS
        command.started_at = datetime.now(UTC)
        db.commit()

        # Execute command
        try:
            # Simulate command execution
            if command.command == "sleep":
                seconds = int(command.parameters.get("seconds", 0))
                time.sleep(seconds)
            elif command.command == "echo":
                message = command.parameters.get("message", "")
                logger.info(f"Echo: {message}")
            else:
                raise ValueError(f"Unknown command: {command.command}")

            # Update command status
            command.status = CommandStatus.COMPLETED
            command.completed_at = datetime.now(UTC)
            db.commit()

            # Send success notification
            send_discord_notification.delay(
                f"✅ Command '{command.command}' completed successfully",
                tank_id=tank.id
            )

        except Exception as exc:
            logger.error(f"Error executing command: {str(exc)}")
            command.status = CommandStatus.FAILED
            command.error = str(exc)
            db.commit()

            # Send failure notification
            send_discord_notification.delay(
                f"❌ Command '{command.command}' failed: {str(exc)}",
                tank_id=tank.id
            )

            # Retry if not exceeded max retries
            if self.request.retries < self.max_retries:
                self.retry(exc=exc)
            else:
                send_discord_notification.delay(
                    f"❌ Command '{command.command}' failed after {self.max_retries} retries",
                    tank_id=tank.id
                )

    except Exception as exc:
        logger.error(f"Error processing command: {str(exc)}")
        self.retry(exc=exc)
    finally:
        db.close()

@celery_app.task(queue="commands")
def schedule_command(tank_id: int, command: str, parameters: dict = None) -> int:
    """
    Schedule a command for processing.
    
    Args:
        tank_id: The ID of the tank
        command: The command to execute
        parameters: Optional command parameters
        
    Returns:
        int: The command ID
    """
    db: Session = next(get_sync_db())
    try:
        # Create a new command
        db_command = Command(
            tank_id=tank_id,
            command=command,
            parameters=parameters,
            status=CommandStatus.PENDING
        )
        db.add(db_command)
        db.commit()
        db.refresh(db_command)
        
        # Schedule the command for processing
        process_command.delay(db_command.id)
        
        return db_command.id
        
    except Exception as e:
        logger.error(f"Error scheduling command: {str(e)}")
        db.rollback()
        return -1
    finally:
        db.close()

@celery_app.task(queue="commands")
def update_node_health(tank_id: int, is_healthy: bool) -> None:
    """Update the health status of a tank node."""
    node_health.labels(tank_id=str(tank_id)).set(1 if is_healthy else 0) 