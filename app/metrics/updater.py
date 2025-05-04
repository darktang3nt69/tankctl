# app/metrics/updater.py

from prometheus_client import Gauge
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.tank import Tank
from app.metrics.tank_metrics import tank_online_status
import asyncio

async def update_tank_metrics():
    while True:
        db: Session = SessionLocal()
        try:
            tanks = db.execute(select(Tank)).scalars().all()
            for tank in tanks:
                tank_online_status.labels(
                    # tank_id=str(tank.tank_id),
                    tank_name=tank.tank_name
                ).set(1 if tank.is_online else 0)
        finally:
            db.close()
        await asyncio.sleep(30)  # update every 30 seconds
