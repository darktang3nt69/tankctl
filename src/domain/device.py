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

    temp_threshold_low: float | None = None
    """Configured low temperature threshold (deg C)"""

    temp_threshold_high: float | None = None
    """Configured high temperature threshold (deg C)"""

    device_name: str | None = None
    """User-friendly device name (e.g., 'Living Room Tank')"""

    location: str | None = None
    """Physical location of the device (e.g., 'Living Room', 'Office Desk')"""

    icon_type: str = "fish_bowl"
    """Icon type from predefined set (e.g., 'fish_bowl', 'tropical', 'planted_tank')"""

    description: str | None = None
    """User notes or description for the device"""

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


@dataclass
class LightSchedule:
    """
    Light schedule for a device.

    Controls when lights turn on/off.
    """

    id: int | None = None
    """Database primary key"""

    device_id: str | None = None
    """Device identifier"""

    enabled: bool = True
    """Whether schedule is active"""

    start_time: str = "08:00"
    """Start time in HH:MM format"""

    end_time: str = "20:00"
    """End time in HH:MM format"""

    created_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp when schedule was created"""

    updated_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp when schedule was last updated"""


@dataclass
class WaterSchedule:
    """
    Water change schedule for a device.

    Tracks water change reminders (weekly or custom dates).
    """

    id: int | None = None
    """Database primary key"""

    device_id: str | None = None
    """Device identifier"""

    schedule_type: str = "weekly"  # 'weekly' or 'custom'
    """Schedule type: weekly recurring or custom date"""

    day_of_week: int | None = None
    """Day of week for weekly schedules (0=Sunday, 6=Saturday)"""

    schedule_date: str | None = None
    """Custom date in YYYY-MM-DD format for custom schedules"""

    schedule_time: str = "12:00"
    """Time for water change in HH:MM format"""

    notes: str | None = None
    """Notes about the water change"""

    completed: bool = False
    """Whether this water change was completed"""

    created_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp when schedule was created"""

    updated_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp when schedule was last updated"""
