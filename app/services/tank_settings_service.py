from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.tank_settings import TankSettings
from app.models.tank_schedule_log import TankScheduleLog
from app.schemas.tank_settings import TankSettingsUpdateRequest, TankOverrideRequest
from app.services.command_service import issue_command
from app.utils.discord import send_discord_embed
from app.utils.timezone import IST

def get_or_create_settings(db: Session, tank_id: str) -> TankSettings:
    settings = db.get(TankSettings, tank_id)
    if not settings:
        settings = TankSettings(tank_id=tank_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def update_tank_settings(
    db: Session,
    tank_id: str,
    payload: TankSettingsUpdateRequest
) -> TankSettings:
    settings = get_or_create_settings(db, tank_id)

    # apply only what changed
    if payload.light_on is not None:
        settings.light_on = payload.light_on
    if payload.light_off is not None:
        settings.light_off = payload.light_off
    if payload.is_schedule_enabled is not None:
        settings.is_schedule_enabled = payload.is_schedule_enabled

    # clear any outstanding override or pause
    settings.schedule_paused_until    = None
    settings.last_schedule_check_on   = None
    settings.last_schedule_check_off  = None

    db.add(settings)
    db.commit()
    db.refresh(settings)

    send_discord_embed(
        status="info",
        tank_name=settings.tank.tank_name,
        extra_fields={
            "Tank ID":           str(settings.tank_id),
            "Light On (IST)":    settings.light_on.strftime("%H:%M"),
            "Light Off (IST)":   settings.light_off.strftime("%H:%M"),
            "Schedule Enabled?": settings.is_schedule_enabled,
            "Paused Until":      "—",
        }
    )
    return settings

def manual_override_command(
    db: Session,
    payload: TankOverrideRequest
) -> TankSettings:
    """
    One‑shot override: fire immediate command, then
    pause scheduling until the *next* opposite edge.
    """
    settings = get_or_create_settings(db, str(payload.tank_id))
    now      = datetime.now(IST)
    today    = now.date()

    # build today’s on/off datetimes as IST‑aware
    on_dt  = datetime.combine(today, settings.light_on).replace(tzinfo=IST)
    off_dt = datetime.combine(today, settings.light_off).replace(tzinfo=IST)

    cmd = payload.override_command  # "light_on" or "light_off"

    if cmd == "light_off":
        # 1) fire off
        issue_command(db, payload.tank_id, "light_off")
        # 2) pause until next ON edge
        next_edge = on_dt if now < on_dt else on_dt + timedelta(days=1)
    elif cmd == 'light_on':  # "on"
        issue_command(db, payload.tank_id, "light_on")
        # pause until next OFF edge
        next_edge = off_dt if now < off_dt else off_dt + timedelta(days=1)

    # store the pause marker
    settings.schedule_paused_until = next_edge

    # log + notify
    log = TankScheduleLog(
        tank_id        = payload.tank_id,
        event_type     = payload.override_command,
        trigger_source = "manual"
    )
    db.add_all([settings, log])
    db.commit()
    db.refresh(settings)

    send_discord_embed(
        status          = f"manual_light_{payload.override_command}",
        tank_name       = settings.tank.tank_name,
        command_payload = payload.override_command,
        extra_fields    = {
            "Paused Until": next_edge.strftime("%Y-%m-%d %H:%M")
        }
    )
    return settings