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
    print("\n" + "=" * 90)
    print(f"⏰ [{now.strftime('%Y-%m-%d %H:%M:%S %Z')}] Running lighting schedule enforcement...")
    try:
        tanks = db.execute(select(Tank).join(TankSettings)).scalars().all()
        print(f"🔍 Found {len(tanks)} tanks to evaluate.\n")

        for tank in tanks:
            settings = tank.settings

            # 1. Skip if scheduler paused
            if not settings.is_schedule_enabled:
                print(f"   ⏸️ Tank {tank.tank_name}: schedule paused; skipping.\n")
                continue

            # 2. Sanity: need both times
            if not settings.light_on or not settings.light_off:
                print(f"   ⚠️ Tank {tank.tank_name}: missing on/off times; skipping.\n")
                continue

            # strip tzinfo so we compare just HH:MM
            on_t = settings.light_on.replace(tzinfo=None)
            off_t = settings.light_off.replace(tzinfo=None)
            ov     = settings.manual_override_state

            print(f"--- Evaluating Tank '{tank.tank_name}' (ID={tank.tank_id}) ---")
            print(f"    Schedule: ON at {on_t}, OFF at {off_t}")
            print(f"    Now (naive): {now_time}")
            print(f"    Manual override: {ov}")

            def inside_window():
                if on_t < off_t:
                    return on_t <= now_time < off_t
                return now_time >= on_t or now_time < off_t

            inside = inside_window()
            print(f"    ➡ Inside window? {inside}")

            # ─── INSIDE ───
            if inside:
                # 3a. Clear any stale override
                if ov is not None:
                    print("    🔄 Clearing manual override; back to schedule")
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

                # 3b. Fire ON exactly once per day
                already_on = (settings.last_schedule_check_on 
                              and settings.last_schedule_check_on.date() == now.date())
                if ov != "off" and not already_on:
                    print("    ✅ Triggering LIGHT ON (scheduled)")
                    # reset any previous OFF so we can re-fire OFF later
                    settings.last_schedule_check_off = None

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
                else:
                    print("    ℹ️ LIGHT ON already handled for today or override=off")
            # ─── OUTSIDE ───
            else:
                # 4a. Clear override if present
                if ov is not None:
                    print("    🔄 Clearing manual override; back to schedule")
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

                # 4b. Only OFF after we’ve done ON today
                on_today = (settings.last_schedule_check_on 
                            and settings.last_schedule_check_on.date() == now.date())
                print(f"    Already ON today? {on_today}")

                already_off = (settings.last_schedule_check_off 
                               and settings.last_schedule_check_off.date() == now.date())
                if ov != "on" and on_today and not already_off:
                    print("    🌙 Triggering LIGHT OFF (scheduled)")
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
                else:
                    print("    ℹ️ LIGHT OFF skipped (either not ON yet or already OFF today)")

            print()  # blank line between tanks

        db.commit()
        print("✅ Lighting schedule enforcement complete.")
        print("=" * 90 + "\n")

    except Exception as e:
        print(f"❌ Schedule executor error: {e}")
        db.rollback()
    finally:
        db.close()
