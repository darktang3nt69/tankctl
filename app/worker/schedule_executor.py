import os
from datetime import datetime
from sqlalchemy.orm import Session
from celery import Celery
import asyncio

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
def enforce_lighting_schedule_sync():
    asyncio.run(_enforce_lighting_schedule_async())

async def _enforce_lighting_schedule_async():
    # current IST timestamp
    now = datetime.now(IST)
    now_ist_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    now_time = now.time()

    print(f"\n=== DEBUG: Starting schedule enforcement at {now_ist_str} ===")
    db: Session = SessionLocal()
    try:
        tanks = db.query(Tank).join(TankSettings).all()
        print(f"DEBUG: Found {len(tanks)} tanks to evaluate\n")

        for tank in tanks:
            settings = tank.settings

            # build IST‑aware datetimes for logging
            lo_dt_ist       = datetime.combine(now.date(), settings.light_on).replace(tzinfo=IST)
            off_dt_ist      = datetime.combine(now.date(), settings.light_off).replace(tzinfo=IST)
            pause_dt_ist    = settings.schedule_paused_until.astimezone(IST) if settings.schedule_paused_until else None
            last_on_ist     = settings.last_schedule_check_on.astimezone(IST) if settings.last_schedule_check_on else None
            last_off_ist    = settings.last_schedule_check_off.astimezone(IST) if settings.last_schedule_check_off else None

            print(f"--- DEBUG: Tank '{tank.tank_name}' (ID={tank.tank_id}) ---")
            print(f"  light_on  (IST) = {lo_dt_ist.strftime('%H:%M')}")
            print(f"  light_off (IST) = {off_dt_ist.strftime('%H:%M')}")
            print(f"  paused_until (IST) = {pause_dt_ist.strftime('%Y-%m-%d %H:%M:%S') if pause_dt_ist else '—'}")
            print(f"  last_on       (IST) = {last_on_ist.strftime('%Y-%m-%d %H:%M:%S') if last_on_ist else '—'}")
            print(f"  last_off      (IST) = {last_off_ist.strftime('%Y-%m-%d %H:%M:%S') if last_off_ist else '—'}")
            print(f"  now_time      (IST) = {now_time.strftime('%H:%M')}")

            # 1) skip if paused
            if pause_dt_ist and now < settings.schedule_paused_until:
                print(f"  DEBUG: Skipping – paused until {pause_dt_ist.strftime('%Y-%m-%d %H:%M:%S')}")
                continue

            # 2) resume if pause expired
            if pause_dt_ist and now >= settings.schedule_paused_until:
                print("  DEBUG: Pause expired – clearing pause and markers")
                settings.schedule_paused_until   = None
                settings.last_schedule_check_on  = None
                settings.last_schedule_check_off = None
                db.add(settings)
                db.commit()

            # 3) skip if disabled or missing times
            if not settings.is_schedule_enabled:
                print("  DEBUG: Skipping – scheduling disabled")
                continue

            # determine inside‑window in IST
            def inside_window():
                if lo_dt_ist < off_dt_ist:
                    return lo_dt_ist.time() <= now_time < off_dt_ist.time()
                return now_time >= lo_dt_ist.time() or now_time < off_dt_ist.time()

            inside = inside_window()
            print(f"  DEBUG: inside_window? {inside}")

            # INSIDE → scheduled ON
            if inside:
                already_on = (settings.last_schedule_check_on
                              and settings.last_schedule_check_on.date() == now.date())
                print(f"  DEBUG: already_on_today? {already_on}")
                if not already_on:
                    print("  DEBUG: Triggering scheduled LIGHT ON")
                    await issue_command(db, tank.tank_id, "light_on")
                    settings.last_schedule_check_on = now
                    db.add(TankScheduleLog(
                        tank_id        = tank.tank_id,
                        event_type     = "light_on",
                        trigger_source = "scheduled"
                    ))
                    await send_discord_embed(
                        status="light_on",
                        tank_name=tank.tank_name,
                        command_payload="light_on (scheduled)"
                    )
                else:
                    print("  DEBUG: LIGHT ON already handled today")

            # OUTSIDE → scheduled OFF
            else:
                on_today     = (settings.last_schedule_check_on
                                and settings.last_schedule_check_on.date() == now.date())
                already_off  = (settings.last_schedule_check_off
                                and settings.last_schedule_check_off.date() == now.date())
                print(f"  DEBUG: on_today? {on_today}, already_off_today? {already_off}")
                if on_today and not already_off:
                    print("  DEBUG: Triggering scheduled LIGHT OFF")
                    await issue_command(db, tank.tank_id, "light_off")
                    settings.last_schedule_check_off = now
                    db.add(TankScheduleLog(
                        tank_id        = tank.tank_id,
                        event_type     = "light_off",
                        trigger_source = "scheduled"
                    ))
                    await send_discord_embed(
                        status="light_off",
                        tank_name=tank.tank_name,
                        command_payload="light_off (scheduled)"
                    )
                else:
                    print("  DEBUG: LIGHT OFF skipped")

            print()  # blank line

        db.commit()
        print("=== DEBUG: Schedule enforcement complete ===\n")

    except Exception as e:
        db.rollback()
        print(f"❌ DEBUG: Schedule executor error: {e}")
    finally:
        db.close()
