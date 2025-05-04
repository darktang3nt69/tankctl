# app/worker/command_dispatcher.py

import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from celery import Celery

from app.core.database import SessionLocal
from app.models.tank_command import TankCommand
from app.utils.discord import send_discord_notification
from app.utils.timezone import IST

celery = Celery(
    "command_dispatcher",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

@celery.task
def command_retry_handler():
    now = datetime.now(IST)
    print(f"🔁 [{now.strftime('%Y-%m-%d %H:%M:%S')}] Running command retry handler...")

    db: Session = SessionLocal()
    try:
        pending_commands = db.execute(
            select(TankCommand)
            .where(TankCommand.status == "pending")
            .where(TankCommand.next_retry_at <= now)
        ).scalars().all()

        for command in pending_commands:
            if command.retries >= 3:
                print(f"❌ Command {command.command_id} failed after 3 retries.")
                command.status = "failed"
                send_discord_notification(
                    status="command_failed",
                    tank_name=command.tank.tank_name,
                    command_payload=command.command_payload
                )
            else:
                command.retries += 1
                backoff_minutes = 2 ** command.retries
                command.next_retry_at = now + timedelta(minutes=backoff_minutes)

                print(f"🔁 Retrying command {command.command_id} | Retries: {command.retries}")

        db.commit()

    except Exception as e:
        print(f"❌ Command retry handler error: {e}")
        db.rollback()
    finally:
        db.close()
