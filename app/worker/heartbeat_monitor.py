# app/worker/heartbeat_monitor.py

import os
from datetime import datetime, timedelta,timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.tank import Tank
from app.utils.discord import send_discord_notification
from app.utils.timezone import IST
from celery import Celery

# Celery app setup
celery = Celery(
    "heartbeat_monitor",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

@celery.task
def heartbeat_check():
    now = datetime.now(IST)
    print(f"🔎 [{now.strftime('%Y-%m-%d %H:%M:%S')}] Running heartbeat check...")

    db: Session = SessionLocal()
    try:
        cutoff = now - timedelta(minutes=2)
        tanks = db.execute(select(Tank)).scalars().all()

        for tank in tanks:
            # Ensure last_seen is timezone aware
            last_seen = (
            tank.last_seen.replace(tzinfo=timezone.utc).astimezone(IST)
            if tank.last_seen.tzinfo is None
                else tank.last_seen.astimezone(IST)
            )

        # Now safe to use last_seen (always IST-aware)
            was_online = tank.is_online
            is_online_now = last_seen >= cutoff

            print(
                f"🔸 Tank: {tank.tank_name:<30} | Was Online: {str(was_online):<5} | Now Online: {str(is_online_now):<5} | Last Seen: {last_seen.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            if was_online and not is_online_now:
                print(f"⚠️  Tank '{tank.tank_name}' went OFFLINE!")
                tank.is_online = False
                send_discord_notification(status="offline", tank_name=tank.tank_name)

            elif not was_online and is_online_now:
                print(f"✅ Tank '{tank.tank_name}' came ONLINE!")
                tank.is_online = True
                send_discord_notification(status="online", tank_name=tank.tank_name)

        db.commit()

    except Exception as e:
        print(f"❌ Heartbeat check error: {e}")
        db.rollback()

    finally:
        db.close()
