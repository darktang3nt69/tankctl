# app/worker/notify_offline_tanks.py

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from celery import Celery
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.tank import Tank
from app.models.tank_alert_status import TankAlertState
from app.utils.discord import send_discord_embed

# ──────────────────────────────────────────────────────
# Celery app setup (same broker/backend as your other tasks)
celery = Celery(
    "notify_offline_tanks",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

# Use IST for all time calculations
IST = ZoneInfo("Asia/Kolkata")

# Read thresholds from env (or fallback)
OFFLINE_THRESHOLD = int(os.getenv("OFFLINE_ALERT_THRESHOLD_SECONDS", "40"))
REPEAT_INTERVAL  = int(os.getenv("OFFLINE_ALERT_REPEAT_MINUTES", "5"))

@celery.task
def notify_offline_tanks():
    """
    Checks each tank’s last_seen timestamp against now (both IST‑aware),
    and sends a Discord alert if it’s been offline too long.
    """
    db: Session = SessionLocal()
    try:
        # Make 'now' timezone‑aware in IST
        now = datetime.now(IST)

        offline_cutoff = timedelta(seconds=OFFLINE_THRESHOLD)
        repeat_cutoff  = timedelta(minutes=REPEAT_INTERVAL)

        print("=" * 80)
        print(f"🔎 [{now.strftime('%Y-%m-%d %H:%M:%S IST')}] Checking for offline tanks…")
        print("=" * 80)

        tanks = db.query(Tank).all()
        for tank in tanks:
            if tank.last_seen is None:
                # never seen this tank—skip
                continue

            # ─── Normalize last_seen to an IST‑aware datetime ───
            last_seen = tank.last_seen

            if last_seen.tzinfo is None:
                # If naive, assume it was stored in UTC:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            # Convert to IST timezone
            last_seen = last_seen.astimezone(IST)

            # Compute how long it’s been offline
            offline_for = now - last_seen

            if offline_for > offline_cutoff:
                # Check when we last sent an alert for this tank
                alert = (
                    db.query(TankAlertState)
                      .filter_by(tank_id=tank.tank_id)
                      .first()
                )

                # If never alerted, or enough time has passed since last alert:
                if not alert or (now - alert.last_alert_sent >= repeat_cutoff):
                    # Build extra fields for Discord embed
                    extra = {
                        "Last Seen (IST)":  last_seen.strftime("%Y-%m-%d %H:%M:%S"),
                        "Offline Duration": str(offline_for).split(".")[0],
                    }
                    send_discord_embed(
                        status="offline",
                        tank_name=tank.tank_name,
                        extra_fields=extra
                    )
                    print(f"⚠️  Alerted offline: {tank.tank_name}")

                    # Record the timestamp of this alert
                    if alert:
                        alert.last_alert_sent = now
                    else:
                        db.add(
                            TankAlertState(
                                tank_id=tank.tank_id,
                                last_alert_sent=now
                            )
                        )

        db.commit()
        print("✅ Offline notifications cycle complete.")
        print("=" * 80)

    except Exception as e:
        # Log the exception and rollback
        print(f"❌ notify_offline_tanks error: {e}")
        db.rollback()
    finally:
        db.close()
