"""
Repository layer for light schedules.

Handles database access for light schedule CRUD operations.
"""

from datetime import time
from typing import Optional

from sqlalchemy.orm import Session

from src.domain.light_schedule import LightSchedule
from src.infrastructure.db.models import LightScheduleModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LightScheduleRepository:
    """Repository for light schedule operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, schedule: LightSchedule) -> LightSchedule:
        """
        Create a new light schedule or update if exists.

        Args:
            schedule: LightSchedule domain model

        Returns:
            Created or updated schedule

        Raises:
            Exception: If creation fails
        """
        try:
            # Check if schedule exists
            existing = self.session.query(LightScheduleModel).filter(
                LightScheduleModel.device_id == schedule.device_id
            ).first()

            if existing:
                # Update existing
                existing.on_time = schedule.on_time
                existing.off_time = schedule.off_time
                existing.enabled = schedule.enabled
                db_schedule = existing
                logger.debug(f"Updating light schedule for device: {schedule.device_id}")
            else:
                # Create new
                db_schedule = LightScheduleModel(
                    device_id=schedule.device_id,
                    on_time=schedule.on_time,
                    off_time=schedule.off_time,
                    enabled=schedule.enabled,
                )
                self.session.add(db_schedule)
                logger.debug(f"Creating light schedule for device: {schedule.device_id}")

            self.session.commit()
            self.session.refresh(db_schedule)

            return self._to_domain(db_schedule)

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create/update schedule: {e}")
            raise

    def get_by_device_id(self, device_id: str) -> Optional[LightSchedule]:
        """
        Get light schedule for a device.

        Args:
            device_id: Device identifier

        Returns:
            LightSchedule or None if not found
        """
        try:
            db_schedule = self.session.query(LightScheduleModel).filter(
                LightScheduleModel.device_id == device_id
            ).first()

            if not db_schedule:
                return None

            return self._to_domain(db_schedule)

        except Exception as e:
            logger.error(f"Failed to get schedule: {e}")
            return None

    def get_all_enabled(self) -> list[LightSchedule]:
        """
        Get all enabled light schedules.

        Returns:
            List of enabled schedules
        """
        try:
            db_schedules = self.session.query(LightScheduleModel).filter(
                LightScheduleModel.enabled == True
            ).all()

            return [self._to_domain(s) for s in db_schedules]

        except Exception as e:
            logger.error(f"Failed to get enabled schedules: {e}")
            return []

    def delete(self, device_id: str) -> bool:
        """
        Delete a light schedule.

        Args:
            device_id: Device identifier

        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.session.query(LightScheduleModel).filter(
                LightScheduleModel.device_id == device_id
            ).delete()

            self.session.commit()

            if result > 0:
                logger.debug(f"Deleted schedule for device: {device_id}")
                return True

            return False

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete schedule: {e}")
            return False

    def _to_domain(self, db_schedule: LightScheduleModel) -> LightSchedule:
        """Convert database model to domain model."""
        return LightSchedule(
            device_id=db_schedule.device_id,
            on_time=db_schedule.on_time,
            off_time=db_schedule.off_time,
            enabled=db_schedule.enabled,
            created_at=db_schedule.created_at,
            updated_at=db_schedule.updated_at,
        )
