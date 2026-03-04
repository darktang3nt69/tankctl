"""
Domain model for device shadow state.

The device shadow represents the desired and reported state of a device.
It enables eventual consistency between backend commands and device state.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DeviceShadow:
    """
    Device shadow state model.

    Each device has a shadow tracking:
    - desired: state the backend wants
    - reported: state the device actually has
    - version: version number for idempotency
    """

    device_id: str
    """Unique device identifier"""

    desired: dict = field(default_factory=dict)
    """Desired state (backend -> device)"""

    reported: dict = field(default_factory=dict)
    """Reported state (device -> backend)"""

    version: int = 0
    """Version number for command idempotency"""

    created_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp when shadow was created"""

    updated_at: datetime = field(default_factory=datetime.utcnow)
    """Timestamp of last shadow update"""

    def is_synchronized(self) -> bool:
        """
        Check if desired and reported states are synchronized.

        Returns:
            True if desired == reported
        """
        return self.desired == self.reported

    def increment_version(self) -> int:
        """
        Increment and return next version number.

        Returns:
            New version number
        """
        self.version += 1
        self.updated_at = datetime.utcnow()
        return self.version

    def update_desired(self, state: dict) -> None:
        """
        Update desired state.

        Args:
            state: New desired state
        """
        self.desired = state
        self.increment_version()

    def update_reported(self, state: dict) -> None:
        """
        Update reported state from device.

        Args:
            state: New reported state from device
        """
        self.reported = state
        self.updated_at = datetime.utcnow()

    def get_delta(self) -> dict:
        """
        Get the difference between desired and reported.

        Returns:
            Dictionary of differences (empty if synchronized)

        Example:
            if desired={light: on} and reported={light: off}
            returns {light: on}
        """
        if self.desired == self.reported:
            return {}

        delta = {}
        for key, desired_value in self.desired.items():
            reported_value = self.reported.get(key)
            if desired_value != reported_value:
                delta[key] = desired_value

        return delta
