"""
Device service layer.

Handles business logic for device operations: registration, status tracking, heartbeats.
"""

from datetime import datetime
from typing import Optional
import secrets

from sqlalchemy.orm import Session

from src.domain.device import Device
from src.domain.device_shadow import DeviceShadow
from src.infrastructure.db.database import db
from src.infrastructure.events.event_publisher import event_publisher
from src.domain.event import device_registered_event, device_online_event, device_offline_event
from src.repository.device_repository import (
    DeviceRepository,
    DeviceShadowRepository,
    WarningAcknowledgementRepository,
)
from src.repository.light_schedule_repository import LightScheduleRepository
from src.repository.telemetry_repository import CommandRepository, TelemetryRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_device_secret(length: int = 16) -> str:
    """
    Generate a cryptographically secure random device secret.
    
    Args:
        length: Length of the secret (default 16 characters)
    
    Returns:
        Random hex string suitable for device authentication
    """
    return secrets.token_hex(length // 2)


class DeviceService:
    """Service for device business logic."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize service with optional session."""
        self.session = session or db.get_session()
        self.device_repo = DeviceRepository(self.session)
        self.shadow_repo = DeviceShadowRepository(self.session)
        self.warning_ack_repo = WarningAcknowledgementRepository(self.session)

    def register_device(
        self,
        device_id: str,
    ) -> Device:
        """
        Register a new device.

        AUTO-GENERATES a secure device_secret that must be provisioned into the device.

        Args:
            device_id: Unique device identifier

        Returns:
            Registered device with auto-generated secret

        Raises:
            ValueError: If device already exists
        """
        logger.info("device_registration_started", device_id=device_id)

        # Check if device already exists
        existing = self.device_repo.get_by_id(device_id)
        if existing:
            logger.warning("device_already_exists", device_id=device_id)
            raise ValueError(f"Device {device_id} already registered")

        # Generate secure secret
        device_secret = generate_device_secret()

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
        
        # Publish device_registered event
        event = device_registered_event(device_id=device_id)
        event_publisher.publish(event)
        
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

    def handle_heartbeat(
        self,
        device_id: str,
        uptime_ms: int | None = None,
        rssi: int | None = None,
        wifi_status: str | None = None,
        firmware_version: str | None = None,
    ) -> None:
        """
        Handle device heartbeat message.

        Marks device as online and updates last_seen.

        Args:
            device_id: Device ID
            uptime_ms: Device uptime in milliseconds
            rssi: WiFi signal strength in dBm
            wifi_status: WiFi connection status string
        """
        device = self.device_repo.get_by_id(device_id)
        if not device:
            logger.warning("heartbeat_device_not_found", device_id=device_id)
            return

        # Mark device as online and update heartbeat diagnostics
        was_offline = device.status != "online"
        device.mark_online()
        if uptime_ms is not None:
            device.uptime_ms = uptime_ms
        if rssi is not None:
            device.rssi = rssi
        if wifi_status is not None:
            device.wifi_status = wifi_status
        if firmware_version is not None:
            device.firmware_version = firmware_version
        self.device_repo.update(device)

        logger.debug("device_heartbeat_received", device_id=device_id)
        
        # Publish device_online only on offline -> online transition
        if was_offline:
            event = device_online_event(device_id=device_id)
            event_publisher.publish(event)

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
                
                # Publish device_online event
                event = device_online_event(device_id=device.device_id)
                event_publisher.publish(event)

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
                
                # Publish device_offline event
                event = device_offline_event(device_id=device.device_id)
                event_publisher.publish(event)

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

    def delete_device(self, device_id: str, scheduler=None) -> dict[str, int | bool | str]:
        """
        Delete a device and all corresponding data.

        Args:
            device_id: Device ID
            scheduler: Optional APScheduler instance for removing schedule jobs

        Returns:
            Summary of deleted records

        Raises:
            ValueError: If the device does not exist
        """
        if not self.device_repo.get_by_id(device_id):
            logger.warning("delete_device_not_found", device_id=device_id)
            raise ValueError(f"Device {device_id} not found")

        schedule_deleted = False
        if scheduler is not None:
            from src.services.scheduling_service import SchedulingService

            schedule_deleted = SchedulingService(self.session, scheduler).delete_schedule(device_id)
        else:
            schedule_deleted = LightScheduleRepository(self.session).delete(device_id)

        commands_deleted = CommandRepository(self.session).delete_for_device(device_id)
        events_deleted = self.device_repo.delete_events(device_id)
        shadow_deleted = self.shadow_repo.delete(device_id)
        device_deleted = self.device_repo.delete(device_id)

        telemetry_session = db.get_timescale_session()
        try:
            telemetry_deleted = TelemetryRepository(telemetry_session).delete_for_device(device_id)
        finally:
            telemetry_session.close()

        logger.info(
            "device_and_related_data_deleted",
            device_id=device_id,
            device_deleted=device_deleted,
            shadow_deleted=shadow_deleted,
            schedule_deleted=schedule_deleted,
            commands_deleted=commands_deleted,
            telemetry_deleted=telemetry_deleted,
            events_deleted=events_deleted,
        )

        return {
            "device_id": device_id,
            "device_deleted": device_deleted,
            "shadow_deleted": shadow_deleted,
            "schedule_deleted": schedule_deleted,
            "commands_deleted": commands_deleted,
            "telemetry_deleted": telemetry_deleted,
            "events_deleted": events_deleted,
        }

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def update_thresholds(
        self,
        device_id: str,
        temp_threshold_low: float | None,
        temp_threshold_high: float | None,
    ) -> Device:
        """Update per-device chart/alert thresholds."""
        if (
            temp_threshold_low is not None
            and temp_threshold_high is not None
            and temp_threshold_low >= temp_threshold_high
        ):
            raise ValueError("temp_threshold_low must be less than temp_threshold_high")

        return self.device_repo.update_thresholds(
            device_id=device_id,
            temp_threshold_low=temp_threshold_low,
            temp_threshold_high=temp_threshold_high,
        )

    def acknowledge_warning(self, device_id: str, warning_code: str) -> None:
        """Persist warning acknowledgement for a specific device/code pair."""
        if not self.device_repo.get_by_id(device_id):
            raise ValueError(f"Device {device_id} not found")
        self.warning_ack_repo.acknowledge(device_id=device_id, warning_code=warning_code)

    def get_acknowledged_warnings(self) -> list[tuple[str, str]]:
        """List all acknowledged warning keys."""
        return self.warning_ack_repo.get_all()

    def update_device_metadata(self, device_id: str, metadata: dict) -> Optional[Device]:
        """Update device metadata (name, location, icon, description, thresholds)."""
        device = self.device_repo.get_by_id(device_id)
        if not device:
            return None

        # Update fields if provided
        if "device_name" in metadata:
            device.device_name = metadata["device_name"]
        if "location" in metadata:
            device.location = metadata["location"]
        if "icon_type" in metadata:
            device.icon_type = metadata["icon_type"]
        if "description" in metadata:
            device.description = metadata["description"]
        if "temp_threshold_low" in metadata:
            device.temp_threshold_low = metadata["temp_threshold_low"]
        if "temp_threshold_high" in metadata:
            device.temp_threshold_high = metadata["temp_threshold_high"]

        # Update in repository
        return self.device_repo.update(device)

    def get_device_detail(self, device_id: str) -> Optional[dict]:
        """Get complete device detail with all settings and schedules."""
        device = self.device_repo.get_by_id(device_id)
        if not device:
            return None

        # Build detail response with device info, light schedule, water schedules
        from src.infrastructure.db.models import LightScheduleModel, WaterScheduleModel
        
        light_schedule = self.session.query(LightScheduleModel).filter_by(device_id=device_id).first()
        water_schedules = self.session.query(WaterScheduleModel).filter_by(device_id=device_id).all()

        return {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "location": device.location,
            "icon_type": device.icon_type,
            "description": device.description,
            "status": device.status,
            "firmware_version": device.firmware_version,
            "created_at": device.created_at.isoformat() if device.created_at else None,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "uptime_ms": device.uptime_ms,
            "rssi": device.rssi,
            "wifi_status": device.wifi_status,
            "temp_threshold_low": device.temp_threshold_low,
            "temp_threshold_high": device.temp_threshold_high,
            "light_schedule": {
                "id": light_schedule.id,
                "device_id": light_schedule.device_id,
                "enabled": light_schedule.enabled,
                "start_time": str(light_schedule.on_time),
                "end_time": str(light_schedule.off_time),
                "created_at": light_schedule.created_at.isoformat() if light_schedule.created_at else None,
                "updated_at": light_schedule.updated_at.isoformat() if light_schedule.updated_at else None,
            } if light_schedule else None,
            "water_schedules": [
                {
                    "id": ws.id,
                    "device_id": ws.device_id,
                    "schedule_type": ws.schedule_type,
                    "days_of_week": [int(d.strip()) for d in ws.days_of_week.split(",")] if ws.days_of_week else None,
                    "schedule_date": ws.schedule_date.isoformat() if ws.schedule_date else None,
                    "schedule_time": str(ws.schedule_time),
                    "notes": ws.notes,
                    "completed": ws.completed,
                    "enabled": ws.enabled,
                    "created_at": ws.created_at.isoformat() if ws.created_at else None,
                    "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
                }
                for ws in water_schedules
            ],
        }

    def set_light_schedule(self, device_id: str, schedule_data: dict):
        """Create or update light schedule for device."""
        from src.infrastructure.db.models import LightScheduleModel
        from datetime import time

        device = self.device_repo.get_by_id(device_id)
        if not device:
            return None

        # Parse times
        on_time = time.fromisoformat(schedule_data["start_time"])
        off_time = time.fromisoformat(schedule_data["end_time"])

        # Check if schedule exists
        existing = self.session.query(LightScheduleModel).filter_by(device_id=device_id).first()
        
        if existing:
            existing.enabled = schedule_data.get("enabled", True)
            existing.on_time = on_time
            existing.off_time = off_time
            existing.updated_at = datetime.utcnow()
            self.session.commit()
            return existing
        else:
            new_schedule = LightScheduleModel(
                device_id=device_id,
                enabled=schedule_data.get("enabled", True),
                on_time=on_time,
                off_time=off_time,
            )
            self.session.add(new_schedule)
            self.session.commit()
            return new_schedule

    def get_light_schedule(self, device_id: str):
        """Get light schedule for device."""
        from src.infrastructure.db.models import LightScheduleModel
        
        return self.session.query(LightScheduleModel).filter_by(device_id=device_id).first()

    def create_water_schedule(self, device_id: str, schedule_data: dict):
        """Create water change schedule for device."""
        from src.infrastructure.db.models import WaterScheduleModel
        from datetime import time

        device = self.device_repo.get_by_id(device_id)
        if not device:
            return None

        schedule_time = time.fromisoformat(schedule_data["schedule_time"])
        
        # Convert days_of_week list to comma-separated string
        days_of_week_str = None
        if schedule_data.get("days_of_week"):
            days_of_week_str = ",".join(str(d) for d in schedule_data["days_of_week"])

        new_schedule = WaterScheduleModel(
            device_id=device_id,
            schedule_type=schedule_data["schedule_type"],
            days_of_week=days_of_week_str,
            schedule_date=schedule_data.get("schedule_date"),
            schedule_time=schedule_time,
            notes=schedule_data.get("notes"),
            enabled=schedule_data.get("enabled", True),
        )
        self.session.add(new_schedule)
        self.session.commit()
        return new_schedule

    def update_water_schedule(self, device_id: str, schedule_id: int, schedule_data: dict):
        """Update water change schedule for device."""
        from src.infrastructure.db.models import WaterScheduleModel
        from datetime import time as time_type

        schedule = self.session.query(WaterScheduleModel).filter_by(
            id=schedule_id,
            device_id=device_id,
        ).first()

        if not schedule:
            return None

        if "schedule_time" in schedule_data and schedule_data["schedule_time"]:
            schedule.schedule_time = time_type.fromisoformat(schedule_data["schedule_time"])
        if "schedule_type" in schedule_data:
            schedule.schedule_type = schedule_data["schedule_type"]
        if "days_of_week" in schedule_data:
            # Convert days_of_week list to comma-separated string
            if schedule_data["days_of_week"]:
                schedule.days_of_week = ",".join(str(d) for d in schedule_data["days_of_week"])
            else:
                schedule.days_of_week = None
        if "schedule_date" in schedule_data:
            schedule.schedule_date = schedule_data["schedule_date"]
        if "notes" in schedule_data:
            schedule.notes = schedule_data["notes"]
        if "enabled" in schedule_data:
            schedule.enabled = schedule_data["enabled"]

        self.session.commit()
        return schedule

    def get_water_schedules(self, device_id: str) -> list:
        """Get all water schedules for device."""
        from src.infrastructure.db.models import WaterScheduleModel
        
        return self.session.query(WaterScheduleModel).filter_by(device_id=device_id).all()

    def delete_water_schedule(self, device_id: str, schedule_id: int) -> bool:
        """Delete water change schedule."""
        from src.infrastructure.db.models import WaterScheduleModel
        
        schedule = self.session.query(WaterScheduleModel).filter_by(
            id=schedule_id,
            device_id=device_id
        ).first()
        
        if not schedule:
            return False

        self.session.delete(schedule)
        self.session.commit()
        return True
