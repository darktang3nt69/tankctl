"""
Repository layer for devices.

Handles database access for device data following the repository pattern.
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.domain.device import Device
from src.domain.device_shadow import DeviceShadow
from src.infrastructure.db.models import DeviceModel, DeviceShadowModel, EventRecord
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DeviceRepository:
    """Repository for device operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, device: Device) -> Device:
        """
        Create a new device in database.

        Args:
            device: Device domain model

        Returns:
            Created device

        Raises:
            Exception: If device already exists
        """
        try:
            db_device = DeviceModel(
                device_id=device.device_id,
                device_secret=device.device_secret,
                status=device.status,
                firmware_version=device.firmware_version,
                created_at=device.created_at,
                last_seen=device.last_seen,
                uptime_ms=device.uptime_ms,
                rssi=device.rssi,
                wifi_status=device.wifi_status,
            )
            self.session.add(db_device)
            self.session.commit()
            logger.info("device_created", device_id=device.device_id)
            return device
        except Exception as e:
            self.session.rollback()
            logger.error("device_creation_failed", device_id=device.device_id, error=str(e))
            raise

    def get_by_id(self, device_id: str) -> Optional[Device]:
        """
        Get device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device or None if not found
        """
        try:
            db_device = self.session.query(DeviceModel).filter(
                DeviceModel.device_id == device_id
            ).first()

            if not db_device:
                return None

            return Device(
                device_id=db_device.device_id,
                device_secret=db_device.device_secret,
                status=db_device.status,
                firmware_version=db_device.firmware_version,
                created_at=db_device.created_at,
                last_seen=db_device.last_seen,
                uptime_ms=db_device.uptime_ms,
                rssi=db_device.rssi,
                wifi_status=db_device.wifi_status,
            )
        except Exception as e:
            logger.error("device_get_failed", device_id=device_id, error=str(e))
            raise

    def get_all(self) -> list[Device]:
        """
        Get all devices.

        Returns:
            List of Device objects
        """
        try:
            devices = []
            db_devices = self.session.query(DeviceModel).all()

            for db_device in db_devices:
                devices.append(
                    Device(
                        device_id=db_device.device_id,
                        device_secret=db_device.device_secret,
                        status=db_device.status,
                        firmware_version=db_device.firmware_version,
                        created_at=db_device.created_at,
                        last_seen=db_device.last_seen,
                        uptime_ms=db_device.uptime_ms,
                        rssi=db_device.rssi,
                        wifi_status=db_device.wifi_status,
                    )
                )

            return devices
        except Exception as e:
            logger.error("devices_get_all_failed", error=str(e))
            raise

    def update(self, device: Device) -> Device:
        """
        Update an existing device.

        Args:
            device: Updated device domain model

        Returns:
            Updated device

        Raises:
            Exception: If device not found
        """
        try:
            db_device = self.session.query(DeviceModel).filter(
                DeviceModel.device_id == device.device_id
            ).first()

            if not db_device:
                raise ValueError(f"Device {device.device_id} not found")

            db_device.status = device.status
            db_device.firmware_version = device.firmware_version
            db_device.last_seen = device.last_seen
            db_device.uptime_ms = device.uptime_ms
            db_device.rssi = device.rssi
            db_device.wifi_status = device.wifi_status

            self.session.commit()
            logger.info("device_updated", device_id=device.device_id)
            return device
        except Exception as e:
            self.session.rollback()
            logger.error("device_update_failed", device_id=device.device_id, error=str(e))
            raise

    def update_last_seen(self, device_id: str) -> None:
        """
        Update device's last_seen timestamp.

        Args:
            device_id: Device ID
        """
        try:
            db_device = self.session.query(DeviceModel).filter(
                DeviceModel.device_id == device_id
            ).first()

            if db_device:
                db_device.last_seen = datetime.utcnow()
                self.session.commit()
                logger.debug("device_last_seen_updated", device_id=device_id)
        except Exception as e:
            self.session.rollback()
            logger.error("device_last_seen_update_failed", device_id=device_id, error=str(e))

    def update_status(self, device_id: str, status: str) -> None:
        """
        Update device status.

        Args:
            device_id: Device ID
            status: New status (online/offline)
        """
        try:
            db_device = self.session.query(DeviceModel).filter(
                DeviceModel.device_id == device_id
            ).first()

            if db_device:
                db_device.status = status
                self.session.commit()
                logger.info("device_status_updated", device_id=device_id, status=status)
        except Exception as e:
            self.session.rollback()
            logger.error("device_status_update_failed", device_id=device_id, error=str(e))

    def delete(self, device_id: str) -> bool:
        """
        Delete a device.

        Args:
            device_id: Device ID
        """
        try:
            deleted = self.session.query(DeviceModel).filter(
                DeviceModel.device_id == device_id
            ).delete()
            self.session.commit()
            logger.info("device_deleted", device_id=device_id, deleted=deleted > 0)
            return deleted > 0
        except Exception as e:
            self.session.rollback()
            logger.error("device_deletion_failed", device_id=device_id, error=str(e))
            raise

    def delete_events(self, device_id: str) -> int:
        """
        Delete stored events for a device.

        Args:
            device_id: Device ID

        Returns:
            Number of deleted event rows
        """
        try:
            deleted = self.session.query(EventRecord).filter(
                EventRecord.device_id == device_id
            ).delete()
            self.session.commit()
            logger.info("device_events_deleted", device_id=device_id, count=deleted)
            return deleted
        except Exception as e:
            self.session.rollback()
            logger.error("device_events_delete_failed", device_id=device_id, error=str(e))
            raise


class DeviceShadowRepository:
    """Repository for device shadow operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, shadow: DeviceShadow) -> DeviceShadow:
        """
        Create a new device shadow.

        Args:
            shadow: DeviceShadow domain model

        Returns:
            Created shadow
        """
        try:
            db_shadow = DeviceShadowModel(
                device_id=shadow.device_id,
                desired=json.dumps(shadow.desired),
                reported=json.dumps(shadow.reported),
                version=shadow.version,
                created_at=shadow.created_at,
                updated_at=shadow.updated_at,
            )
            self.session.add(db_shadow)
            self.session.commit()
            logger.info("shadow_created", device_id=shadow.device_id)
            return shadow
        except Exception as e:
            self.session.rollback()
            logger.error("shadow_creation_failed", device_id=shadow.device_id, error=str(e))
            raise

    def get_by_device_id(self, device_id: str) -> Optional[DeviceShadow]:
        """
        Get device shadow by device ID.

        Args:
            device_id: Device ID

        Returns:
            DeviceShadow or None if not found
        """
        try:
            db_shadow = self.session.query(DeviceShadowModel).filter(
                DeviceShadowModel.device_id == device_id
            ).first()

            if not db_shadow:
                return None

            return DeviceShadow(
                device_id=db_shadow.device_id,
                desired=json.loads(db_shadow.desired),
                reported=json.loads(db_shadow.reported),
                version=db_shadow.version,
                created_at=db_shadow.created_at,
                updated_at=db_shadow.updated_at,
            )
        except Exception as e:
            logger.error("shadow_get_failed", device_id=device_id, error=str(e))
            raise

    def update(self, shadow: DeviceShadow) -> DeviceShadow:
        """
        Update device shadow.

        Args:
            shadow: Updated DeviceShadow domain model

        Returns:
            Updated shadow

        Raises:
            Exception: If shadow not found
        """
        try:
            db_shadow = self.session.query(DeviceShadowModel).filter(
                DeviceShadowModel.device_id == shadow.device_id
            ).first()

            if not db_shadow:
                raise ValueError(f"Shadow for device {shadow.device_id} not found")

            db_shadow.desired = json.dumps(shadow.desired)
            db_shadow.reported = json.dumps(shadow.reported)
            db_shadow.version = shadow.version
            db_shadow.updated_at = shadow.updated_at

            self.session.commit()
            logger.debug("shadow_updated", device_id=shadow.device_id, version=shadow.version)
            return shadow
        except Exception as e:
            self.session.rollback()
            logger.error("shadow_update_failed", device_id=shadow.device_id, error=str(e))
            raise

    def update_reported(self, device_id: str, reported_state: dict) -> Optional[DeviceShadow]:
        """
        Update reported state in shadow.

        Args:
            device_id: Device ID
            reported_state: New reported state from device

        Returns:
            Updated shadow or None if not found
        """
        try:
            db_shadow = self.session.query(DeviceShadowModel).filter(
                DeviceShadowModel.device_id == device_id
            ).first()

            if not db_shadow:
                return None

            db_shadow.reported = json.dumps(reported_state)
            db_shadow.updated_at = datetime.utcnow()

            self.session.commit()
            logger.debug("shadow_reported_updated", device_id=device_id)

            return DeviceShadow(
                device_id=db_shadow.device_id,
                desired=json.loads(db_shadow.desired),
                reported=reported_state,
                version=db_shadow.version,
                created_at=db_shadow.created_at,
                updated_at=db_shadow.updated_at,
            )
        except Exception as e:
            self.session.rollback()
            logger.error("shadow_reported_update_failed", device_id=device_id, error=str(e))
            raise

    def delete(self, device_id: str) -> bool:
        """
        Delete a device shadow.

        Args:
            device_id: Device ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            deleted = self.session.query(DeviceShadowModel).filter(
                DeviceShadowModel.device_id == device_id
            ).delete()
            self.session.commit()
            logger.info("shadow_deleted", device_id=device_id, deleted=deleted > 0)
            return deleted > 0
        except Exception as e:
            self.session.rollback()
            logger.error("shadow_delete_failed", device_id=device_id, error=str(e))
            raise
