"""
Task Scheduler - APScheduler wrapper for background jobs.

Manages periodic tasks:
- Shadow reconciliation (10s)
- Device health monitoring (30s)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from src.config.settings import settings
from src.infrastructure.db.database import db
from src.services.device_service import DeviceService
from src.services.shadow_service import ShadowService
from src.services.water_schedule_reminder_service import WaterScheduleReminderService
from src.services.push_notification_service import PushNotificationService
from src.repository.device_push_token_repository import DevicePushTokenRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TankCtlScheduler:
    """Background task scheduler for TankCtl."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = BackgroundScheduler(
            timezone=ZoneInfo(settings.app.timezone)
        )
        self._is_running = False
        self._reminder_service = WaterScheduleReminderService()
    
    def start(self):
        """
        Start scheduler and register jobs.
        
        Jobs:
        - _reconcile_shadows_job: Every 10 seconds
        - _check_device_health_job: Every 30 seconds
        """
        try:
            logger.info("scheduler_starting")
            
            # Register shadow reconciliation job (every 10s)
            self.scheduler.add_job(
                self._reconcile_shadows_job,
                trigger=IntervalTrigger(seconds=settings.scheduler.shadow_reconciliation_interval),
                id="reconcile_shadows",
                name="Shadow Reconciliation",
                replace_existing=True,
            )
            logger.info(
                "job_registered",
                job_id="reconcile_shadows",
                interval=f"{settings.scheduler.shadow_reconciliation_interval}s",
            )
            
            # Register device health check job (every 30s)
            self.scheduler.add_job(
                self._check_device_health_job,
                trigger=IntervalTrigger(seconds=settings.scheduler.offline_detection_interval),
                id="check_device_health",
                name="Device Health Check",
                replace_existing=True,
            )
            logger.info(
                "job_registered",
                job_id="check_device_health",
                interval=f"{settings.scheduler.offline_detection_interval}s",
            )

            # Register water schedule reminder job (every 60s)
            self.scheduler.add_job(
                self._check_water_schedule_reminders_job,
                trigger=IntervalTrigger(seconds=60),
                id="check_water_reminders",
                name="Water Schedule Reminders",
                replace_existing=True,
            )
            logger.info("job_registered", job_id="check_water_reminders", interval="60s")

            self.scheduler.start()
            self._is_running = True
            logger.info("scheduler_started")
            
        except Exception as e:
            logger.error("scheduler_start_error", error=str(e))
            raise
    
    def stop(self):
        """Stop scheduler and cancel all jobs."""
        try:
            logger.info("scheduler_stopping")
            
            if self._is_running and self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                self._is_running = False
                logger.info("scheduler_stopped")
            
        except Exception as e:
            logger.error("scheduler_stop_error", error=str(e))
    
    def _reconcile_shadows_job(self):
        """
        Periodic job: Reconcile device shadows.
        
        For all devices, check if desired != reported and publish commands.
        This job runs every 10 seconds.
        """
        try:
            session = db.get_session()
            
            try:
                shadow_service = ShadowService(session)
                device_service = DeviceService(session)
                
                # Get all devices
                devices = device_service.get_all_devices()
                
                for device in devices:
                    try:
                        # Get shadow
                        shadow = device_service.get_device_shadow(device.device_id)
                        
                        if shadow and not shadow.is_synchronized():
                            # Reconcile (publish command)
                            updated_shadow = shadow_service.reconcile_shadow(device.device_id)
                            
                            logger.info(
                                "shadow_reconciled",
                                device_id=device.device_id,
                                version=updated_shadow.version if updated_shadow else None,
                            )
                    
                    except Exception as e:
                        logger.error(
                            "shadow_reconciliation_failed",
                            device_id=device.device_id,
                            error=str(e),
                        )
                        continue
            
            finally:
                session.close()
        
        except Exception as e:
            logger.error("reconcile_shadows_job_error", error=str(e))
    
    def _check_device_health_job(self):
        """
        Periodic job: Check device health and detect offline devices.
        
        Mark devices as offline if no heartbeat received within timeout.
        This job runs every 30 seconds.
        """
        try:
            session = db.get_session()
            
            try:
                device_service = DeviceService(session)
                
                # Check health of all devices with configured timeout
                status_changes = device_service.check_device_health(
                    timeout_seconds=settings.scheduler.device_offline_timeout
                )
                
                if status_changes:
                    logger.info(
                        "device_status_changes",
                        count=len(status_changes),
                        changes=status_changes,
                    )
            
            finally:
                session.close()
        
        except Exception as e:
            logger.error("check_device_health_job_error", error=str(e))

    def _check_water_schedule_reminders_job(self):
        """
        Periodic job: Send FCM push notifications for upcoming water changes.

        Runs every 60 seconds.  For each enabled, incomplete water schedule the
        reminder service evaluates whether a 24-h, 1-h, or on-time notification
        should fire right now (wall-clock IST).
        
        Respects notification preferences (notify_24h, notify_1h, notify_on_time).
        Logs skipped reminders due to user preferences.
        """
        try:
            from src.infrastructure.db.models import WaterScheduleModel, DeviceModel

            session = db.get_session()
            try:
                schedules = (
                    session.query(WaterScheduleModel)
                    .filter_by(enabled=True, completed=False)
                    .all()
                )

                due = self._reminder_service.get_due_reminders(schedules)
                
                # Map of reminder_type to preference column name
                reminder_prefs = {
                    "day_before": "notify_24h",
                    "hour_before": "notify_1h",
                    "on_time": "notify_on_time",
                }
                
                # Log skipped reminders (due to preferences being False)
                for schedule in schedules:
                    for reminder_type, pref_name in reminder_prefs.items():
                        pref_value = getattr(schedule, pref_name, True)
                        if not pref_value:
                            logger.info(
                                "water_reminder_skipped_preference",
                                device_id=schedule.device_id,
                                schedule_id=schedule.id,
                                reminder_type=reminder_type,
                                preference=pref_name,
                                reason=f"{pref_name}=False",
                            )
                
                if not due:
                    return

                token_repo = DevicePushTokenRepository(session)
                push_service = PushNotificationService(
                    token_repo,
                    settings.fcm_service_account_json,
                    settings.fcm_project_id,
                )

                for schedule, reminder_type in due:
                    try:
                        device = session.get(DeviceModel, schedule.device_id)
                        device_name = device.device_name if device else None

                        title, body = self._reminder_service.build_notification(
                            device_name, schedule.device_id, schedule, reminder_type
                        )
                        
                        # Pass reminder_type to FCM payload
                        data = {
                            "reminder_type": reminder_type,
                            "schedule_id": str(schedule.id),
                            "device_id": schedule.device_id,
                        }

                        sent = push_service.broadcast_fcm(
                            schedule.device_id, title, body,
                            data=data,
                            notification_type="water_change",
                        )
                        logger.info(
                            "water_reminder_sent",
                            device_id=schedule.device_id,
                            schedule_id=schedule.id,
                            reminder_type=reminder_type,
                            sent=sent,
                        )
                    except Exception as e:
                        logger.error(
                            "water_reminder_error",
                            schedule_id=schedule.id,
                            reminder_type=reminder_type,
                            device_id=schedule.device_id,
                            error=str(e),
                        )
            finally:
                session.close()

        except Exception as e:
            logger.error("check_water_reminders_job_error", error=str(e))
