# app/worker/celery_app.py

import os
from celery import Celery

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
}

celery.conf.timezone = "Asia/Kolkata"
