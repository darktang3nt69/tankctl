"""
Celery configuration for TankCTL.

This module sets up the Celery application with Redis as the broker and backend.
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tankctl",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",
    include=["app.tasks.commands"]
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery configuration
celery_app.conf.update(
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default"
        },
        "commands": {
            "exchange": "commands",
            "routing_key": "commands"
        },
        "notifications": {
            "exchange": "notifications",
            "routing_key": "notifications"
        }
    }
) 