"""
MQTT message handlers for TankCtl.

Handlers implement the MessageHandler interface and route incoming MQTT messages to services.
"""

from src.infrastructure.db.database import db
from src.infrastructure.mqtt.mqtt_client import MessageHandler
from src.services.device_service import DeviceService
from src.services.shadow_service import ShadowService
from src.services.telemetry_service import TelemetryService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HeartbeatHandler(MessageHandler):
    """Handle device heartbeat messages."""

    def handle(self, device_id: str, payload: dict) -> None:
        """
        Handle heartbeat from device.

        Marks device as online and updates last_seen.

        Args:
            device_id: Device ID
            payload: Heartbeat payload from device
        """
        try:
            session = db.get_session()
            service = DeviceService(session)

            service.handle_heartbeat(device_id)

            logger.info("device_heartbeat_handled", device_id=device_id)
            session.close()
        except Exception as e:
            logger.error("heartbeat_handler_error", device_id=device_id, error=str(e))


class ReportedStateHandler(MessageHandler):
    """Handle device reported state messages."""

    def handle(self, device_id: str, payload: dict) -> None:
        """
        Handle reported state from device.

        Updates shadow with device's current state.

        Args:
            device_id: Device ID
            payload: Reported state from device
        """
        try:
            session = db.get_session()
            shadow_service = ShadowService(session)
            device_service = DeviceService(session)

            # Mark device as online
            device_service.handle_heartbeat(device_id)

            # Update shadow with reported state
            shadow_service.handle_reported_state(device_id, payload)

            logger.info("reported_state_handled", device_id=device_id)
            session.close()
        except Exception as e:
            logger.error("reported_state_handler_error", device_id=device_id, error=str(e))


class TelemetryHandler(MessageHandler):
    """Handle device telemetry messages."""

    def handle(self, device_id: str, payload: dict) -> None:
        """
        Handle telemetry from device.

        Stores telemetry data in TimescaleDB.

        Args:
            device_id: Device ID
            payload: Telemetry data from device
        """
        try:
            # Use telemetry session
            session = db.get_timescale_session()
            service = TelemetryService(session)

            # Store telemetry
            service.store_telemetry(device_id, payload)

            # Also mark device as online (heartbeat behavior)
            db_session = db.get_session()
            device_service = DeviceService(db_session)
            device_service.handle_heartbeat(device_id)
            db_session.close()

            logger.debug("telemetry_handled", device_id=device_id)
            session.close()
        except Exception as e:
            logger.error("telemetry_handler_error", device_id=device_id, error=str(e))
