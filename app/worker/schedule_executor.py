import os
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import select
from celery import Celery
from app.core.database import SessionLocal
from app.models.tank import Tank
from app.models.tank_settings import TankSettings
from app.models.tank_schedule_log import TankScheduleLog
from app.services.command_service import issue_command
from app.utils.discord import send_discord_notification
from app.utils.timezone import IST

celery = Celery(
    "schedule_executor",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

@celery.task(name="app.worker.schedule_executor.enforce_lighting_schedule")
def enforce_lighting_schedule():
    now = datetime.now(IST)
    now_time = now.time()

    db: Session = SessionLocal()
    print("=" * 90)
    print(f"⏰ [{now.strftime('%Y-%m-%d %H:%M:%S')}] Running lighting schedule enforcement...")

    try:
        tanks = db.execute(select(Tank).join(TankSettings)).scalars().all()

        for tank in tanks:
            settings = tank.settings
            if not settings or not settings.light_on or not settings.light_off:
                continue

            light_on_time = settings.light_on
            light_off_time = settings.light_off
            override = settings.manual_override_state

            def is_within_schedule():
                if light_on_time < light_off_time:
                    return light_on_time <= now_time < light_off_time
                else:
                    # Overnight window (e.g., 20:00 to 06:00)
                    return now_time >= light_on_time or now_time < light_off_time

            inside_window = is_within_schedule()

            # 💡 1. INSIDE SCHEDULE WINDOW
            if inside_window:
                if override is not None:
                    print(f"🔄 Tank {tank.tank_name}: Cleared manual override. Schedule resumes control.")
                    settings.manual_override_state = None

                    # Discord + DB log for override cleared
                    send_discord_notification(
                        status="override_cleared",
                        tank_name=tank.tank_name,
                        command_payload="Manual override cleared — control returned to schedule"
                    )
                    db.add(TankScheduleLog(
                        tank_id=tank.tank_id,
                        event_type="override_cleared",
                        trigger_source="scheduled"
                    ))

                if override != "off" and (
                    not settings.last_schedule_check_on or settings.last_schedule_check_on.date() != now.date()
                ):
                    print(f"✅ Tank {tank.tank_name}: Triggering LIGHT ON (schedule)")
                    issue_command(db, tank.tank_id, "light_on")
                    settings.last_schedule_check_on = now

                    send_discord_notification(
                        status="light_on",
                        tank_name=tank.tank_name,
                        command_payload="light_on (scheduled)"
                    )
                    db.add(TankScheduleLog(
                        tank_id=tank.tank_id,
                        event_type="light_on",
                        trigger_source="scheduled"
                    ))

            # 💡 2. OUTSIDE SCHEDULE WINDOW
            else:
                if override is not None:
                    print(f"🔄 Tank {tank.tank_name}: Cleared manual override. Schedule resumes control.")
                    settings.manual_override_state = None

                    send_discord_notification(
                        status="override_cleared",
                        tank_name=tank.tank_name,
                        command_payload="Manual override cleared — control returned to schedule"
                    )
                    db.add(TankScheduleLog(
                        tank_id=tank.tank_id,
                        event_type="override_cleared",
                        trigger_source="scheduled"
                    ))

                if override != "on" and (
                    not settings.last_schedule_check_off or settings.last_schedule_check_off.date() != now.date()
                ):
                    print(f"🌙 Tank {tank.tank_name}: Triggering LIGHT OFF (schedule)")
                    issue_command(db, tank.tank_id, "light_off")
                    settings.last_schedule_check_off = now

                    send_discord_notification(
                        status="light_off",
                        tank_name=tank.tank_name,
                        command_payload="light_off (scheduled)"
                    )
                    db.add(TankScheduleLog(
                        tank_id=tank.tank_id,
                        event_type="light_off",
                        trigger_source="scheduled"
                    ))

        db.commit()
        print("✅ Lighting schedule enforcement complete.")
        print("=" * 90)

    except Exception as e:
        print(f"❌ Schedule executor error: {e}")
        db.rollback()
    finally:
        db.close()
