"""
Command service layer.

Handles business logic for sending commands to devices.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.domain.command import Command, CommandStatus
from src.infrastructure.db.database import db
from src.infrastructure.mqtt.mqtt_client import mqtt_client
from src.infrastructure.mqtt.mqtt_topics import MQTTTopics
from src.infrastructure.events.event_publisher import event_publisher
from src.domain.event import command_sent_event, command_executed_event, command_failed_event
from src.repository.telemetry_repository import CommandRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CommandService:
    """Service for command business logic."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize service with optional session."""
        self.session = session or db.get_session()
        self.repo = CommandRepository(self.session)

    def send_command(
        self,
        device_id: str,
        command: str,
        value: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Command:
        """
        Send a command to a device.

        Creates command record and publishes to MQTT.

        Args:
            device_id: Target device ID
            command: Command name (e.g., 'set_light', 'reboot_device')
            value: Optional command parameter
            version: Optional version number (auto-incremented if not provided)

        Returns:
            Created command

        Raises:
            Exception: If command sending fails
        """
        logger.info(
            "command_sending",
            device_id=device_id,
            command=command,
        )

        try:
            # Use provided version or auto-increment
            if version is None:
                # Get highest version + 1
                latest = self.repo.get_latest_for_device(device_id, limit=1)
                version = (latest[0].version + 1) if latest else 1

            # Create command domain model
            cmd = Command(
                device_id=device_id,
                command=command,
                value=value,
                version=version,
                status=CommandStatus.PENDING,
            )

            # Store in database
            self.repo.create(cmd)

            # Publish to MQTT
            topic = MQTTTopics.command_topic(device_id)
            payload = cmd.to_mqtt_payload()

            mqtt_client.publish(topic, payload, qos=1, retain=False)

            # Mark as sent
            cmd.mark_sent()

            if cmd.id is not None:
                updated = self.repo.update_status(cmd.id, CommandStatus.SENT)
                if updated:
                    cmd = updated

            logger.info(
                "command_sent",
                device_id=device_id,
                command=command,
            )
            
            # Publish command_sent event
            event = command_sent_event(
                device_id=device_id,
                command=command,
                value=value,
                version=version,
            )
            event_publisher.publish(event)

            return cmd

        except Exception as e:
            logger.error(
                "command_send_failed",
                device_id=device_id,
                command=command,
                error=str(e),
            )
            raise

    def get_pending_commands(self, device_id: str) -> list[Command]:
        """
        Get all pending commands for a device.

        Args:
            device_id: Device ID

        Returns:
            List of pending commands
        """
        return self.repo.get_pending_for_device(device_id)

    def get_command_history(self, device_id: str, limit: int = 20) -> list[Command]:
        """
        Get command history for a device.

        Args:
            device_id: Device ID
            limit: Maximum number of commands to return

        Returns:
            List of recent commands (newest first)
        """
        return self.repo.get_latest_for_device(device_id, limit=limit)

    def mark_command_executed(self, command_id: int) -> Optional[Command]:
        """
        Mark a command as successfully executed by device.

        Args:
            command_id: Command ID

        Returns:
            Updated command or None if not found
        """
        logger.debug("marking_command_executed", command_id=command_id)
        updated = self.repo.update_status(command_id, CommandStatus.EXECUTED)
        
        if updated:
            # Publish command_executed event
            event = command_executed_event(
                device_id=updated.device_id,
                command=updated.command,
                command_id=command_id,
            )
            event_publisher.publish(event)
        
        return updated

    def mark_command_failed(self, command_id: int) -> Optional[Command]:
        """
        Mark a command as failed.

        Args:
            command_id: Command ID

        Returns:
            Updated command or None if not found
        """
        logger.warning("marking_command_failed", command_id=command_id)
        updated = self.repo.update_status(command_id, CommandStatus.FAILED)
        
        if updated:
            # Publish command_failed event
            event = command_failed_event(
                device_id=updated.device_id,
                command=updated.command,
                command_id=command_id,
            )
            event_publisher.publish(event)
        
        return updated

    def close(self) -> None:
        """Close the session."""
        self.session.close()
