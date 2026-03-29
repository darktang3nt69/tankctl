"""
Domain model for firmware releases.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class FirmwareRelease:
    """Firmware release information."""

    id: Optional[int] = None
    version: str = ""
    filename: str = ""
    file_size: int = 0
    checksum: Optional[str] = None
    platform: str = "esp32"  # esp32, arduino
    release_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FirmwareDeployment:
    """Firmware deployment status for a device."""

    id: Optional[int] = None
    release_id: int = 0
    device_id: str = ""
    status: str = "pending"  # pending, updating, success, failed
    error_message: Optional[str] = None
    command_version: Optional[int] = None
    attempted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
