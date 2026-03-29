"""
Shadow reconciliation service.

Handles shadow state reconciliation between desired and reported state.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.domain.device_shadow import DeviceShadow
from src.infrastructure.db.database import db
from src.infrastructure.events.event_publisher import event_publisher
from src.domain.event import shadow_drifted_event, shadow_synchronized_event, Event
from src.services.command_service import CommandService
from src.repository.device_repository import DeviceShadowRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ShadowService:
    """Service for device shadow reconciliation."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize service with optional session."""
        self.session = session or db.get_session()
        self.shadow_repo = DeviceShadowRepository(self.session)

    def reconcile_shadow(self, device_id: str) -> Optional[DeviceShadow]:
        """
        Reconcile device shadow.

        If desired != reported, sends a command to bring device into desired state.

        Args:
            device_id: Device ID to reconcile
        """
        logger.debug("shadow_reconciliation_started", device_id=device_id)

        try:
            shadow = self.shadow_repo.get_by_device_id(device_id)
            if not shadow:
                logger.warning("shadow_not_found", device_id=device_id)
                return None

            # Check if already synchronized
            if shadow.is_synchronized():
                logger.debug("shadow_already_synchronized", device_id=device_id)
                return shadow

            # Get delta between desired and reported
            delta = shadow.get_delta()
            if not delta:
                logger.debug("shadow_delta_empty", device_id=device_id)
                return shadow

            logger.info(
                "shadow_reconciliation_needed",
                device_id=device_id,
                delta=delta,
            )
            
            # Publish shadow_drifted event
            event = shadow_drifted_event(
                device_id=device_id,
                version=shadow.version,
                delta=delta,
            )
            event_publisher.publish(event)

            command_service = CommandService(self.session)

            for key, desired_value in delta.items():
                command_name = f"set_{key}"
                command_value = str(desired_value)

                command_service.send_command(
                    device_id=device_id,
                    command=command_name,
                    value=command_value,
                    version=shadow.version,
                )

                logger.debug(
                    "shadow_delta_command_sent",
                    device_id=device_id,
                    key=key,
                    desired=desired_value,
                    reported=shadow.reported.get(key),
                    command=command_name,
                )

            return shadow

        except Exception as e:
            logger.error("shadow_reconciliation_failed", device_id=device_id, error=str(e))
            return None

def handle_reported_state(
        self,
        device_id: str,
        reported_state: dict,
    ) -> Optional[DeviceShadow]:
        """
        Handle reported state update from device.

        Updates the reported state in shadow and checks for reconciliation.

        Args:
            device_id: Device ID
            reported_state: Reported state from device

        Returns:
            Updated shadow or None if not found
        """
        logger.debug("handling_reported_state", device_id=device_id)

        try:
            # Get old state before updating
            old_shadow = self.shadow_repo.get_by_device_id(device_id)
            old_light_state = old_shadow.reported.get("light") if old_shadow else None
            
            # Update reported state
            shadow = self.shadow_repo.update_reported(device_id, reported_state)
            if shadow:
                was_drifted = not shadow.is_synchronized() or (shadow.desired != reported_state)
                
                logger.debug(
                    "shadow_reported_state_updated",
                    device_id=device_id,
                    synchronized=shadow.is_synchronized(),
                )
                
                # Publish light_state_changed event if light state actually changed
                new_light_state = reported_state.get("light")
                if new_light_state and new_light_state != old_light_state:
                    event = Event(
                        event="light_state_changed",
                        device_id=device_id,
                        metadata={
                            "light": new_light_state,
                            "_from_reconciliation": False,
                        }
                    )
                    event_publisher.publish(event)
                    logger.info("light_state_changed_event_published", device_id=device_id, light=new_light_state)
                
                # Check if shadow just became synchronized
                if shadow.is_synchronized():
                    # Publish shadow_synchronized event
                    event = shadow_synchronized_event(
                        device_id=device_id,
                        version=shadow.version,
                    )
                    event_publisher.publish(event)
            return shadow
        except Exception as e:
            logger.error("handle_reported_state_failed", device_id=device_id, error=str(e))
            raise

    def set_desired_state(self, device_id: str, desired_state: dict) -> Optional[DeviceShadow]:
        """
        Set the desired state for a device.

        Args:
            device_id: Device ID
            desired_state: New desired state

        Returns:
            Updated shadow or None if not found
        """
        logger.info("setting_desired_state", device_id=device_id)

        try:
            shadow = self.shadow_repo.get_by_device_id(device_id)
            if not shadow:
                logger.warning("shadow_not_found", device_id=device_id)
                return None

            shadow.update_desired(desired_state)
            updated = self.shadow_repo.update(shadow)

            logger.info(
                "desired_state_updated",
                device_id=device_id,
                version=updated.version,
            )

            return updated
        except Exception as e:
            logger.error("set_desired_state_failed", device_id=device_id, error=str(e))
            raise

    def close(self) -> None:
        """Close the session."""
        self.session.close()


# Alias for backwards compatibility
ShadowRepository = DeviceShadowRepository
