import os
from datetime import datetime, timedelta
import requests
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.tank import Tank
from app.worker.celery_app import celery
from app.utils.discord import send_discord_notification

@celery.task
def heartbeat_check():
    print("🔎 Running heartbeat check...")

    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        threshold_minutes = int(os.getenv("TANK_OFFLINE_THRESHOLD_MINUTES", 2))
        cutoff = now - timedelta(minutes=threshold_minutes)

        tanks = db.execute(select(Tank)).scalars().all()

        for tank in tanks:
            was_online = tank.is_online
            is_online_now = tank.last_seen >= cutoff

            if was_online and not is_online_now:
                print(f"⚠️ Tank {tank.tank_name} went OFFLINE")
                tank.is_online = False
                send_discord_notification(
                    tank_name=f"{tank.tank_name}",
                    status="offline"
                )
            elif not was_online and is_online_now:
                print(f"✅ Tank {tank.tank_name} came ONLINE")
                tank.is_online = True
                send_discord_notification(
                    tank_name=f"{tank.tank_name}",
                    status="online"
                )

        db.commit()

    except Exception as e:
        print(f"❌ Heartbeat check error: {e}")
        db.rollback()
    finally:
        db.close()
