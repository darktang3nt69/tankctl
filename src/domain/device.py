"""
Domain model for devices.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Device:
    """
    Device domain model.

    Represents a TankCtl IoT device with stable identity and tracking.
    """

    device_id: str
    """Unique device identifier (e.g., 'tank1', 'greenhouse-light-1')"""

    device_secret: str
    """Authentication secret for MQTT connection"""

    status: str = "offline"
    """Current device status: online | offline"""

    firmware_version: str | None = None
    """Current firmware version running on device"""

    created_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp when device was registered"""

    last_seen: datetime = field(default_factory=datetime.utcnow)
    """Timestamp of last heartbeat or activity"""

    uptime_ms: int | None = None
    """Device uptime in milliseconds from last boot"""

    rssi: int | None = None
    """WiFi signal strength in dBm"""

    wifi_status: str | None = None
    """WiFi connection status string from device"""

    def is_online(self, timeout_seconds: int = 60) -> bool:
        """
        Check if device is currently online.

        Args:
            timeout_seconds: Seconds since last_seen to consider offline

        Returns:
            True if device is online, False otherwise
        """
        if self.status == "offline":
            return False

        elapsed = (datetime.utcnow() - self.last_seen).total_seconds()
        return elapsed < timeout_seconds

    def mark_online(self) -> None:
        """Mark device as online and update last_seen."""
        self.status = "online"
        self.last_seen = datetime.utcnow()

    def mark_offline(self) -> None:
        """Mark device as offline."""
        self.status = "offline"
