"""
Light scheduling service.

Manages light schedules and integrates with APScheduler to update device shadows.
"""

from datetime import time, datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.domain.light_schedule import LightSchedule
from src.infrastructure.db.database import db
from src.repository.light_schedule_repository import LightScheduleRepository
from src.services.shadow_service import ShadowService
from src.utils.datetime_utils import now_in_app_timezone
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SchedulingService:
    """Service for light schedule management."""

    def __init__(self, session: Optional[Session] = None, scheduler=None):
        """
        Initialize scheduling service.
        
        Args:
            session: Optional database session
            scheduler: Optional APScheduler instance (TankCtlScheduler)
        """
        self.session = session or db.get_session()
        self.schedule_repo = LightScheduleRepository(self.session)
        self.scheduler = scheduler

    def create_schedule(
        self,
        device_id: str,
        on_time: time,
        off_time: time,
        enabled: bool = True,
    ) -> LightSchedule:
        """
        Create or update a light schedule for a device.
        
        This creates the schedule in the database and registers APScheduler jobs
        if a scheduler is available.
        
        Args:
            device_id: Device identifier
            on_time: Time to turn light on (e.g., time(18, 0))
            off_time: Time to turn light off (e.g., time(6, 0))
            enabled: Whether schedule is active
            
        Returns:
            Created/updated LightSchedule
        """
        logger.info(
            "creating_light_schedule",
            device_id=device_id,
            on_time=str(on_time),
            off_time=str(off_time),
            enabled=enabled,
        )

        # Create domain model
        schedule = LightSchedule(
            device_id=device_id,
            on_time=on_time,
            off_time=off_time,
            enabled=enabled,
        )

        # Save to database
        saved_schedule = self.schedule_repo.create(schedule)

        # Register with APScheduler if available
        if self.scheduler and enabled:
            self._register_scheduler_jobs(saved_schedule)

        logger.info("light_schedule_created", device_id=device_id)
        
        # Apply current desired state immediately
        self._apply_current_state(saved_schedule)

        return saved_schedule

    def get_schedule(self, device_id: str) -> Optional[LightSchedule]:
        """
        Get light schedule for a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            LightSchedule or None
        """
        return self.schedule_repo.get_by_device_id(device_id)

    def delete_schedule(self, device_id: str) -> bool:
        """
        Delete a light schedule.
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if deleted, False otherwise
        """
        logger.info("deleting_light_schedule", device_id=device_id)

        # Remove from APScheduler if available
        if self.scheduler:
            self._unregister_scheduler_jobs(device_id)

        # Delete from database
        result = self.schedule_repo.delete(device_id)

        if result:
            logger.info("light_schedule_deleted", device_id=device_id)

        return result

    def load_all_schedules(self) -> None:
        """
        Load all enabled schedules and register them with APScheduler.
        
        Called on backend startup to restore scheduled jobs.
        """
        if not self.scheduler:
            logger.warning("no_scheduler_available")
            return

        logger.info("loading_all_light_schedules")

        schedules = self.schedule_repo.get_all_enabled()

        for schedule in schedules:
            self._register_scheduler_jobs(schedule)
            # Apply current state for each device
            self._apply_current_state(schedule)

        logger.info(
            "light_schedules_loaded",
            count=len(schedules),
        )

    def _register_scheduler_jobs(self, schedule: LightSchedule) -> None:
        """
        Register APScheduler jobs for a schedule.
        
        Creates two jobs: one for ON time, one for OFF time.
        """
        if not self.scheduler:
            return

        device_id = schedule.device_id

        # Job ID format: light_schedule_{device_id}_{on|off}
        on_job_id = f"light_schedule_{device_id}_on"
        off_job_id = f"light_schedule_{device_id}_off"

        # Remove existing jobs if any
        self._unregister_scheduler_jobs(device_id)

        # Register ON job
        self.scheduler.add_job(
            func=self._set_light_state,
            trigger='cron',
            hour=schedule.on_time.hour,
            minute=schedule.on_time.minute,
            id=on_job_id,
            args=[device_id, "on"],
            replace_existing=True,
        )

        # Register OFF job
        self.scheduler.add_job(
            func=self._set_light_state,
            trigger='cron',
            hour=schedule.off_time.hour,
            minute=schedule.off_time.minute,
            id=off_job_id,
            args=[device_id, "off"],
            replace_existing=True,
        )

        logger.debug(
            "scheduler_jobs_registered",
            device_id=device_id,
            on_time=str(schedule.on_time),
            off_time=str(schedule.off_time),
        )

    def _unregister_scheduler_jobs(self, device_id: str) -> None:
        """Remove APScheduler jobs for a device."""
        if not self.scheduler:
            return

        on_job_id = f"light_schedule_{device_id}_on"
        off_job_id = f"light_schedule_{device_id}_off"

        # Try to remove jobs (ignore if they don't exist)
        try:
            self.scheduler.remove_job(on_job_id)
        except:
            pass

        try:
            self.scheduler.remove_job(off_job_id)
        except:
            pass

        logger.debug("scheduler_jobs_unregistered", device_id=device_id)

    def _set_light_state(self, device_id: str, state: str) -> None:
        """
        Set light state in device shadow (called by APScheduler).
        
        Args:
            device_id: Device identifier
            state: "on" or "off"
        """
        logger.info(
            "schedule_triggered",
            device_id=device_id,
            desired_light=state,
        )

        try:
            # Create a new session for this scheduled task
            session = db.get_session()
            shadow_service = ShadowService(session)

            # Update desired state in shadow
            shadow_service.set_desired_state(
                device_id=device_id,
                desired_state={"light": state},
            )

            session.close()

            logger.info(
                "schedule_applied",
                device_id=device_id,
                light_state=state,
            )

        except Exception as e:
            logger.error(
                "schedule_apply_failed",
                device_id=device_id,
                state=state,
                error=str(e),
            )

    def _apply_current_state(self, schedule: LightSchedule) -> None:
        """
        Apply the current desired state based on schedule.
        
        Called when schedule is created/updated to immediately set correct state.
        """
        current_state = schedule.get_current_desired_state(
            now_in_app_timezone().time()
        )
        
        logger.info(
            "applying_current_schedule_state",
            device_id=schedule.device_id,
            current_state=current_state,
        )

        try:
            shadow_service = ShadowService(self.session)
            shadow_service.set_desired_state(
                device_id=schedule.device_id,
                desired_state={"light": current_state},
            )
        except Exception as e:
            logger.error(
                "apply_current_state_failed",
                device_id=schedule.device_id,
                error=str(e),
            )

    def close(self) -> None:
        """Close the session."""
        self.session.close()
