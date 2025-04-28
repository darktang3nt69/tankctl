# app/core/celeryconfig.py

from celery.schedules import crontab

beat_schedule = {
    # Heartbeat every 1 minute
    "heartbeat-check-every-minute": {
        "task": "app.worker.heartbeat_monitor.heartbeat_check",
        "schedule": crontab(minute="*"),
    },
    # Command retry every 1 minute
    "command-retry-every-minute": {
        "task": "app.worker.command_dispatcher.command_retry_handler",
        "schedule": crontab(minute="*"),
    },
}

timezone = "Asia/Kolkata"  # ✅ IST timezone
