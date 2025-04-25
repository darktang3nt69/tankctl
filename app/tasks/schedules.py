"""
Scheduled tasks for TankCTL.

This module contains periodic Celery tasks for system maintenance and monitoring.
"""

from celery.schedules import crontab
from app.core.celery import celery_app
from app.tasks.notifications import check_tank_health

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "check-tank-health": {
        "task": "app.tasks.notifications.check_tank_health",
        "schedule": 30.0,  # Every 30 seconds
    },
}

# Timezone for scheduled tasks
celery_app.conf.timezone = "UTC" 