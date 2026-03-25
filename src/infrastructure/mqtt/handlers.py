"""
MQTT message handlers for TankCtl.

Handlers implement the MessageHandler interface and route incoming MQTT messages to services.
"""

from src.infrastructure.db.database import db
from src.infrastructure.mqtt.mqtt_client import MessageHandler
from src.domain.command import CommandStatus
from src.services.command_service import CommandService
from src.services.device_service import DeviceService
from src.services.shadow_service import ShadowService
from src.services.telemetry_service import TelemetryService
from src.utils.logger import get_logger

from src.infrastructure.events.event_publisher import event_publisher
from src.domain.event import Event

logger = get_logger(__name__)


class DeviceStatusHandler(MessageHandler):
    """Handle device status/warning messages (e.g. sensor unavailable)."""

    def handle(self, device_id: str, payload: dict) -> None:
        code = payload.get("code", "unknown")
        message = payload.get("message", "")
        logger.warning(
            "device_warning",
            device_id=device_id,
            code=code,
            message=message,
        )
        event_publisher.publish(
            Event(
                event="device_warning",
                device_id=device_id,
                metadata={"code": code, "message": message},
            )
        )


class HeartbeatHandler(MessageHandler):
    """Handle device heartbeat messages."""

    def handle(self, device_id: str, payload: dict) -> None:
        """
        Handle heartbeat from device.

        Marks device as online, updates last_seen, and reconciles shadow state.

        Args:
            device_id: Device ID
            payload: Heartbeat payload from device
        """
        try:
            session = db.get_session()
            service = DeviceService(session)
            
            # Check if device is registered
            device = service.get_device(device_id)
            if not device:
                logger.warning("heartbeat_rejected_unregistered", device_id=device_id)
                session.close()
                return

            service.handle_heartbeat(
                device_id,
                uptime_ms=payload.get("uptime_ms"),
                rssi=payload.get("rssi"),
                wifi_status=payload.get("wifi"),
                firmware_version=payload.get("firmware_version"),
            )

            logger.info("device_heartbeat_handled", device_id=device_id)
            
            # Reconcile shadow state to fix any drift from power loss or disconnections
            # This sends commands to bring device into desired state if needed
            shadow_service = ShadowService(session)
            shadow = shadow_service.reconcile_shadow(device_id)
            if shadow and not shadow.is_synchronized():
                logger.info(
                    "shadow_reconciliation_triggered_by_heartbeat",
                    device_id=device_id,
                    delta=shadow.get_delta(),
                )
            
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
            device_service = DeviceService(session)
            
            # Check if device is registered
            device = device_service.get_device(device_id)
            if not device:
                logger.warning("reported_state_rejected_unregistered", device_id=device_id)
                session.close()
                return

            shadow_service = ShadowService(session)

            # Mark device as online
            device_service.handle_heartbeat(device_id)

            # Update shadow with reported state
            shadow_service.handle_reported_state(device_id, payload)

            # Mark matching open commands as executed based on reported state
            command_service = CommandService(session)
            recent_commands = command_service.get_command_history(device_id, limit=20)

            for command in recent_commands:
                if command.id is None:
                    continue

                if command.status not in (CommandStatus.PENDING, CommandStatus.SENT):
                    continue

                if command.command == "set_light" and payload.get("light") == command.value:
                    command_service.mark_command_executed(command.id)
                elif command.command == "set_pump" and payload.get("pump") == command.value:
                    command_service.mark_command_executed(command.id)

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
            # Check if device is registered first
            check_session = db.get_session()
            device_service = DeviceService(check_session)
            device = device_service.get_device(device_id)
            check_session.close()
            
            if not device:
                logger.warning("telemetry_rejected_unregistered", device_id=device_id)
                return

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
