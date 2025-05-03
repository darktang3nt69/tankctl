# app/services/tank_service.py

import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tank import Tank
from app.models.tank_settings import TankSettings
from app.schemas.tank import TankRegisterRequest, TankRegisterResponse
from app.utils.jwt import create_jwt_token
from app.utils.discord import send_discord_embed
from app.core.config import settings
from app.utils.timezone import IST

def register_tank(db: Session, request: TankRegisterRequest) -> TankRegisterResponse:
    print(f"[DEBUG] incoming auth_key='{request.auth_key}'  |  settings.TANK_PRESHARED_KEY='{settings.TANK_PRESHARED_KEY}'")

    if request.auth_key != settings.TANK_PRESHARED_KEY:
        raise HTTPException(status_code=401, detail="Invalid pre-shared key")

    existing = db.execute(
        select(Tank).where(Tank.tank_name == request.tank_name)
    ).scalar_one_or_none()

    if existing:
    # Always generate a fresh token
        new_token = create_jwt_token(str(existing.tank_id))
        existing.token = new_token
        db.commit()
        return TankRegisterResponse(
            message="Tank re-registered and token refreshed 🔄",
            tank_id=str(existing.tank_id),
            access_token=new_token
        )

    new_id = uuid.uuid4()
    token = create_jwt_token(str(new_id))

    new_tank = Tank(
        tank_id=new_id,
        last_seen=datetime.now(IST),
        is_online=True,
        tank_name=request.tank_name,
        location=request.location,
        firmware_version=request.firmware_version,
        token=token,
    )
    db.add(new_tank)
    db.commit()
    db.refresh(new_tank)

    # 🔥 Create settings row (defaults kick in if request.light_on/off None)
    tank_settings = TankSettings(
        tank_id=new_tank.tank_id,
        light_on=request.light_on,
        light_off=request.light_off
    )
    db.add(tank_settings)
    db.commit()
    db.refresh(tank_settings)

    extra_fields = {
        'Tank ID' : new_tank.tank_id,
        'Tank Name' : new_tank.tank_name,
        'Tank Location' : new_tank.location,
        'Tank Light on at' : tank_settings.light_on,
        'Tank Light off at' : tank_settings.light_off,
        'Firmware Version' : new_tank.firmware_version,
    }

    send_discord_embed(status="new_registration", tank_name=new_tank.tank_name, extra_fields=extra_fields)

    # Return schedule in response
    return TankRegisterResponse(
        message="Tank registered successfully ✅",
        tank_id=str(new_tank.tank_id),
        access_token=token,
        light_on=tank_settings.light_on,
        light_off=tank_settings.light_off,
        is_schedule_enabled=tank_settings.is_schedule_enabled,
        firmware_version=new_tank.firmware_version,
    )
