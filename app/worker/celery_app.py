# app/worker/celery_app.py

import os
from celery import Celery

from app.core.database import SessionLocal
from app.services.command_service import retry_stale_commands

celery = Celery(
    "aquapi",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_BACKEND_URL"),
    include=["app.worker.heartbeat_monitor"],
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
}

celery.conf.timezone = "Asia/Kolkata"


@celery.task
def command_retry_handler():
    db = SessionLocal()
    try:
        retry_stale_commands(db)
    finally:
        db.close()