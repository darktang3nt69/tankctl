from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.discord import send_discord_embed
from app.models.tank import Tank
from app.models.tank_alert_status import TankAlertState
from celery import Celery
import os


# Celery app setup
celery = Celery(
    "notify_offline_tanks",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

@celery.task
def notify_offline_tanks():
    db: Session = next(get_db())

    now = datetime.utcnow()
    threshold = timedelta(seconds=40)

    tanks = db.query(Tank).all()
    for tank in tanks:
        if now - tank.last_seen > threshold:
            # Check last alert
            alert = db.query(TankAlertState).filter_by(tank_id=tank.tank_id).first()

            if not alert or (now - alert.last_alert_sent >= timedelta(minutes=5)):
                # Send Discord Notification
                send_discord_embed(status="offline", tank_name=tank.tank_name)
                # Update or insert alert time
                if alert:
                    alert.last_alert_sent = now
                else:
                    db.add(TankAlertState(tank_id=tank.tank_id, last_alert_sent=now))

    db.commit()
