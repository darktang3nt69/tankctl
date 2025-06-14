# app/worker/celery_app.py

import os
from celery import Celery
import asyncio

from app.core.database import SessionLocal
from app.services.command_service import retry_stale_commands

celery = Celery(
    "aquapi",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_BACKEND_URL"),
    include=["app.worker.heartbeat_monitor", "app.worker.schedule_executor", "app.worker.notify_offline_tanks"],
)

celery.conf.beat_schedule = {
    "heartbeat-check-every-minute": {
        "task": "app.worker.heartbeat_monitor.heartbeat_check",
        "schedule": float(os.getenv("HEARTBEAT_CHECK_INTERVAL_MINUTES", 1)) * 60,
    },
    "retry-commands-every-2-minutes": {
        "task": "app.worker.celery_app.command_retry_handler",
        "schedule": float(os.getenv("COMMAND_RETRY_INTERVAL_MINUTES", 2)) * 60,
    },
    "run-schedule-enforcer-every-minute": {
        "task": "app.worker.schedule_executor.enforce_lighting_schedule_sync",
        "schedule": float(os.getenv("SCHEDULE_LIGHTING_INTERVAL_MINUTES")) * 60,
    },
    "check-offline-tanks-every-5-min": {
        "task": "app.worker.notify_offline_tanks.notify_offline_tanks",
        "schedule": float(os.getenv("CHECK_OFFLINE_TANK_STATUS_INTERVAL_MINUTES")) * 60,  # Every 5 min
    }
}

celery.conf.timezone = "Asia/Kolkata"


@celery.task
def command_retry_handler():
    asyncio.run(_command_retry_handler_async())

async def _command_retry_handler_async():
    db = SessionLocal()
    try:
        await retry_stale_commands(db)
    finally:
        db.close()