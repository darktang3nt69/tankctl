"""
Celery configuration for TankCTL.

This module sets up the Celery application with Redis as broker and PostgreSQL as backend.
"""

from celery import Celery
from app.core.config import settings

redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
if settings.REDIS_PASSWORD:
    redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

celery_app = Celery(
    "tankctl",
    broker=redis_url,
    backend="db+postgresql://postgres:postgres@tankctl_db:5432/tankctl",
    include=["app.tasks.commands", "app.tasks.notifications"]
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_connection_timeout=30,
    broker_pool_limit=None,
    broker_heartbeat=10,
    broker_transport_options={
        'visibility_timeout': 43200,  # 12 hours
    },
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