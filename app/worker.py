import os
from celery import Celery

# Initialize Celery
celery_app = Celery(
    "tankctl",
    broker=os.getenv("REDIS_URL", "redis://:changeme@redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://:changeme@redis:6379/0"),
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_connection_retry_delay=5,
)

# Import tasks
from app.tasks import notifications  # noqa 