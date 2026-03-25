"""
Domain model for commands sent to devices.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CommandStatus(str, Enum):
    """Status of a command."""

    PENDING = "pending"
    SENT = "sent"
    EXECUTED = "executed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Command:
    """
    Command sent to a device.

    Commands must be versioned for idempotency and include:
    - version: for idempotency
    - command: the command name (e.g., 'set_light')
    - value: the command parameter
    """

    device_id: str
    """Target device ID"""

    command: str
    """Command name (e.g., 'set_light', 'reboot_device')"""

    id: int | None = None
    """Database command ID"""

    value: str | None = None
    """Command parameter value"""

    version: int = 0
    """Command version for idempotency"""

    status: str = CommandStatus.PENDING
    """Current command status"""

    created_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp when command was created"""

    sent_at: datetime | None = None
    """Timestamp when command was sent to device"""

    executed_at: datetime | None = None
    """Timestamp when command was acknowledged as executed"""

    def to_mqtt_payload(self) -> dict:
        """
        Convert command to MQTT payload format.

        Returns:
            Dictionary ready for JSON serialization to MQTT
        """
        payload = {
            "version": self.version,
            "command": self.command,
        }
        if self.value is not None:
            payload["value"] = self.value
        
        # Include metadata if present (for commands like firmware updates)
        if hasattr(self, 'metadata') and self.metadata:
            payload.update(self.metadata)
        
        return payload

    def mark_sent(self) -> None:
        """Mark command as sent to device."""
        self.status = CommandStatus.SENT
        self.sent_at = datetime.utcnow()

    def mark_executed(self) -> None:
        """Mark command as executed by device."""
        self.status = CommandStatus.EXECUTED
        self.executed_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Mark command as failed."""
        self.status = CommandStatus.FAILED

    def mark_timeout(self) -> None:
        """Mark command as timed out."""
        self.status = CommandStatus.TIMEOUT
