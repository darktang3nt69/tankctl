"""
Device service layer.

Handles business logic for device operations: registration, status tracking, heartbeats.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.domain.device import Device
from src.domain.device_shadow import DeviceShadow
from src.infrastructure.db.database import db
from src.repository.device_repository import DeviceRepository, DeviceShadowRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DeviceService:
    """Service for device business logic."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize service with optional session."""
        self.session = session or db.get_session()
        self.device_repo = DeviceRepository(self.session)
        self.shadow_repo = DeviceShadowRepository(self.session)

    def register_device(
        self,
        device_id: str,
        device_secret: str,
    ) -> Device:
        """
        Register a new device.

        Args:
            device_id: Unique device identifier
            device_secret: Device authentication secret

        Returns:
            Registered device

        Raises:
            Exception: If device already exists or registration fails
        """
        logger.info("device_registration_started", device_id=device_id)

        # Check if device already exists
        existing = self.device_repo.get_by_id(device_id)
        if existing:
            logger.warning("device_already_exists", device_id=device_id)
            raise ValueError(f"Device {device_id} already registered")

        # Create device
        device = Device(
            device_id=device_id,
            device_secret=device_secret,
            status="offline",
        )

        registered = self.device_repo.create(device)

        # Create associated shadow
        shadow = DeviceShadow(device_id=device_id)
        self.shadow_repo.create(shadow)

        logger.info("device_registered", device_id=device_id)
        return registered

    def get_device(self, device_id: str) -> Optional[Device]:
        """
        Get device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device or None
        """
        return self.device_repo.get_by_id(device_id)

    def get_all_devices(self) -> list[Device]:
        """
        Get all registered devices.

        Returns:
            List of all devices
        """
        return self.device_repo.get_all()

    def handle_heartbeat(self, device_id: str) -> None:
        """
        Handle device heartbeat message.

        Marks device as online and updates last_seen.

        Args:
            device_id: Device ID
        """
        device = self.device_repo.get_by_id(device_id)
        if not device:
            logger.warning("heartbeat_device_not_found", device_id=device_id)
            return

        # Mark device as online
        device.mark_online()
        self.device_repo.update(device)

        logger.debug("device_heartbeat_received", device_id=device_id)

    def check_device_health(self, timeout_seconds: int = 60) -> dict[str, str]:
        """
        Check health of all devices and mark offline if needed.

        Args:
            timeout_seconds: Seconds since last_seen to consider offline

        Returns:
            Dictionary with device_id -> status mapping
        """
        devices = self.device_repo.get_all()
        status_changes = {}

        for device in devices:
            is_online = device.is_online(timeout_seconds)

            # Check if status changed
            should_be_online = is_online
            currently_online = device.status == "online"

            if should_be_online and not currently_online:
                # Device came online
                device.mark_online()
                self.device_repo.update(device)
                status_changes[device.device_id] = "online"
                logger.info("device_came_online", device_id=device.device_id)

            elif not should_be_online and currently_online:
                # Device went offline
                device.mark_offline()
                self.device_repo.update(device)
                status_changes[device.device_id] = "offline"
                logger.warning(
                    "device_went_offline",
                    device_id=device.device_id,
                    last_seen=device.last_seen.isoformat(),
                )

        return status_changes

    def get_device_shadow(self, device_id: str) -> Optional[DeviceShadow]:
        """
        Get device shadow state.

        Args:
            device_id: Device ID

        Returns:
            DeviceShadow or None if not found
        """
        return self.shadow_repo.get_by_device_id(device_id)

    def close(self) -> None:
        """Close the session."""
        self.session.close()
