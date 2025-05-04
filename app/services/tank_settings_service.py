# app/services/tank_settings_service.py

from sqlalchemy.orm import Session
from uuid import UUID

from app.models.tank_settings import TankSettings
from app.models.tank_schedule_log import TankScheduleLog
from app.schemas.tank_settings import TankSettingsUpdateRequest, TankOverrideRequest
from app.services.command_service import issue_command
from app.utils.discord import send_discord_embed


def get_or_create_settings(db: Session, tank_id: str) -> TankSettings:
    """
    Fetch existing settings, or create a default row if missing.
    """
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

    # apply only the fields the client sent
    if payload.light_on is not None:
        settings.light_on = payload.light_on
    if payload.light_off is not None:
        settings.light_off = payload.light_off
    if payload.is_schedule_enabled is not None:
        settings.is_schedule_enabled = payload.is_schedule_enabled

    # --- new additions for full reset on schedule change ---
    # clear manual override…
    settings.manual_override_state = "off"
    # …and clear today's schedule markers
    settings.last_schedule_check_on  = None
    settings.last_schedule_check_off = None
    # ----------------------------------------------------------

    db.add(settings)
    db.commit()
    db.refresh(settings)

    extra = {
        "Tank ID":           str(settings.tank_id),
        "Light On (IST)":    settings.light_on.strftime("%H:%M"),
        "Light Off (IST)":   settings.light_off.strftime("%H:%M"),
        "Schedule Enabled?": settings.is_schedule_enabled,
        "Manual Override?":  settings.manual_override_state,
    }
    send_discord_embed(
        status="info",
        tank_name=settings.tank.tank_name,
        extra_fields=extra
    )

    return settings


def manual_override_command(
    db: Session,
    payload: TankOverrideRequest
) -> TankSettings:
    """
    Issue a manual light_on/light_off command and reset today's schedule
    markers so the next scheduled window can still fire.
    """
    tank_id = str(payload.tank_id)
    settings = get_or_create_settings(db, tank_id)

    # 1) clear today’s schedule so it will retrigger next window
    settings.last_schedule_check_on  = None
    settings.last_schedule_check_off = None

    # 2) record the override state so the scheduler won’t undo it immediately
    settings.manual_override_state = "on"

    # 3) issue the command
    issue_command(db, payload.tank_id, payload.override_command)

    # 4) log & notify
    log = TankScheduleLog(
        tank_id=payload.tank_id,
        event_type=payload.override_command,
        trigger_source="manual"
    )
    db.add_all([settings, log])
    db.commit()
    db.refresh(settings)

    send_discord_embed(
    status=f"manual_light_{settings.manual_override_state}",
    tank_name=settings.tank.tank_name,
    command_payload=payload.override_command,
    extra_fields={
        "Tank ID": tank_id,
        "Command": payload.override_command
    }
)


    return settings
