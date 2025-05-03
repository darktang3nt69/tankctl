import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from celery import Celery

from app.core.database import SessionLocal
from app.models.tank import Tank
from app.models.tank_settings import TankSettings
from app.models.tank_schedule_log import TankScheduleLog
from app.services.command_service import issue_command
from app.utils.discord import send_discord_embed
from app.utils.timezone import IST

# Celery app setup
celery = Celery(
    "schedule_executor",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

@celery.task
def enforce_lighting_schedule():
    now = datetime.now(IST)
    now_time = now.time().replace(tzinfo=None)

    db: Session = SessionLocal()
    print("=" * 90)
    print(f"⏰ [{now.strftime('%Y-%m-%d %H:%M:%S')}] Running lighting schedule enforcement...")
    try:
        # fetch all tanks with their settings
        tanks = db.execute(
            select(Tank).join(TankSettings)
        ).scalars().all()

        for tank in tanks:
            settings = tank.settings

            # 🛑 Skip if schedule is disabled
            if not settings.is_schedule_enabled:
                print(f"⏸️  Tank {tank.tank_name}: schedule is paused, skipping")
                continue

            # 🛠 sanity check
            if not settings.light_on or not settings.light_off:
                continue

            # strip tzinfo so we compare naive HH:MM vs naive HH:MM
            light_on_time  = settings.light_on.replace(tzinfo=None)
            light_off_time = settings.light_off.replace(tzinfo=None)
            override       = settings.manual_override_state

            def is_within_schedule():
                if light_on_time < light_off_time:
                    return light_on_time <= now_time < light_off_time
                else:
                    # overnight window (e.g. 20:00→06:00)
                    return now_time >= light_on_time or now_time < light_off_time

            inside_window = is_within_schedule()

            # 💡 INSIDE window: schedule wants lights ON
            if inside_window:
                # clear a stale manual override
                if override is not None:
                    settings.manual_override_state = None
                    send_discord_embed(
                        status="override_cleared",
                        tank_name=tank.tank_name,
                        command_payload="Manual override cleared — schedule resumed"
                    )
                    db.add(TankScheduleLog(
                        tank_id=tank.tank_id,
                        event_type="override_cleared",
                        trigger_source="scheduled"
                    ))

                # if not already turned on today
                if override != "off" and (
                    not settings.last_schedule_check_on
                    or settings.last_schedule_check_on.date() != now.date()
                ):
                    issue_command(db, tank.tank_id, "light_on")
                    settings.last_schedule_check_on = now

                    send_discord_embed(
                        status="light_on",
                        tank_name=tank.tank_name,
                        command_payload="light_on (scheduled)"
                    )
                    db.add(TankScheduleLog(
                        tank_id=tank.tank_id,
                        event_type="light_on",
                        trigger_source="scheduled"
                    ))

            # 🌙 OUTSIDE window: schedule wants lights OFF
            else:
                if override is not None:
                    settings.manual_override_state = None
                    send_discord_embed(
                        status="override_cleared",
                        tank_name=tank.tank_name,
                        command_payload="Manual override cleared — schedule resumed"
                    )
                    db.add(TankScheduleLog(
                        tank_id=tank.tank_id,
                        event_type="override_cleared",
                        trigger_source="scheduled"
                    ))

                if override != "on" and (
                    not settings.last_schedule_check_off
                    or settings.last_schedule_check_off.date() != now.date()
                ):
                    issue_command(db, tank.tank_id, "light_off")
                    settings.last_schedule_check_off = now

                    send_discord_embed(
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
