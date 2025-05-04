import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.tank import Tank
from app.models.tank_alert_status import TankAlertState
from app.utils.discord import send_discord_embed
from app.utils.timezone import IST
from celery import Celery
import time

from app.metrics.tank_metrics import tank_online_status

# Celery app setup
celery = Celery(
    "heartbeat_monitor",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

@celery.task
def heartbeat_check():
    start_time = time.time()
    now = datetime.now(IST)

    print("=" * 80)
    print(f"🔎 [{now.strftime('%Y-%m-%d %H:%M:%S')}] Starting heartbeat check")
    print("=" * 80)

    db: Session = SessionLocal()
    try:
        cutoff = now - timedelta(minutes=2)
        tanks = db.execute(select(Tank)).scalars().all()
        print(f"📊 Total tanks checked: {len(tanks)}")

        offline_count = 0
        online_count = 0

        for tank in tanks:
            if tank.last_seen is None:
                print(f"⚠️  Tank '{tank.tank_name}' has no last_seen timestamp. Skipping.")
                continue

            # Ensure last_seen is timezone aware
            last_seen = (
                tank.last_seen.replace(tzinfo=timezone.utc).astimezone(IST)
                if tank.last_seen.tzinfo is None
                else tank.last_seen.astimezone(IST)
            )

            was_online = tank.is_online
            is_online_now = last_seen >= cutoff

            # 👇 Prometheus metric for Grafana time series
            tank_online_status.labels(
                tank_name=tank.tank_name
            ).set(1 if is_online_now else 0)

            print(
                f"🔸 Tank: {tank.tank_name:<30} | Was Online: {str(was_online):<5} | Now Online: {str(is_online_now):<5} | Last Seen: {last_seen.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            if was_online and not is_online_now:
                print(f"⚠️  Tank '{tank.tank_name}' went OFFLINE!")
                tank.is_online = False
                offline_count += 1
                send_discord_embed(status="offline", tank_name=tank.tank_name)
                # ✅ Clear alert state if it exists
                existing_alert = db.query(TankAlertState).filter_by(tank_id=tank.tank_id).first()
                if existing_alert:
                    db.delete(existing_alert)
                    db.commit()
                    print(f"🧹 Cleared alert state for '{tank.tank_name}'")

            elif not was_online and is_online_now:
                print(f"✅ Tank '{tank.tank_name}' came ONLINE!")
                tank.is_online = True
                online_count += 1
                send_discord_embed(status="online", tank_name=tank.tank_name)

        db.commit()

        duration = time.time() - start_time
        print("-" * 80)
        print(f"✅ Heartbeat check completed in {duration:.2f} seconds")
        print(f"🔴 Offline changes: {offline_count} | 🟢 Online changes: {online_count}")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Heartbeat check error: {e}")
        db.rollback()

    finally:
        db.close()

