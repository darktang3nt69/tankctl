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

# Refer to JWT (JSON Web Token) RFC 7519: https://datatracker.ietf.org/doc/html/rfc7519
# Refer to PyJWT documentation: https://pyjwt.readthedocs.io/en/stable/

async def register_tank(db: Session, request: TankRegisterRequest) -> TankRegisterResponse:
    """
    Registers a new tank or re-registers an existing tank, issuing a new JWT token.

    Business Logic:
    1.  **Authentication:** Validates the `auth_key` against a pre-shared key defined in settings.
        This is a critical security step to prevent unauthorized tank registrations.
    2.  **Existing Tank Check:** Queries the database to check if a tank with the provided
        `tank_name` already exists. This allows existing tanks to re-register (e.g., after a reboot)
        without creating duplicate entries, simply refreshing their access token.
    3.  **New Tank Registration:** If the tank does not exist:
        - Generates a new unique `tank_id` (UUID).
        - Creates a new JWT `access_token` for the tank.
        - Persists the new `Tank` entry in the database with its initial status (online, last seen).
        - Creates a corresponding `TankSettings` entry with default or provided lighting schedule.
    4.  **Discord Notification:** Sends an embed message to a configured Discord channel
        to notify administrators about a new tank registration.
    5.  **Response:** Returns a `TankRegisterResponse` with the registration details,
        including the new `tank_id` and `access_token`.
    """
    print("[DEBUG] Authentication attempt received for tank registration.")

    # Business Rule: Validate the pre-shared authentication key.
    # This ensures only authorized devices can register as tanks.
    if request.auth_key != settings.TANK_PRESHARED_KEY:
        raise ValueError("Invalid pre-shared key")

    # Business Rule: Check if the tank already exists. If so, re-register and refresh its token.
    # This handles scenarios where a tank might restart or need a new token without creating duplicates.
    existing = db.execute(
        select(Tank).where(Tank.tank_name == request.tank_name)
    ).scalar_one_or_none()

    if existing:
        # Generate a new JWT token for the existing tank.
        new_token = create_jwt_token(str(existing.tank_id))
        existing.token = new_token
        db.commit()
        db.refresh(existing) # Refresh to load updated token

        # Retrieve tank settings to include in the response.
        existing_settings = db.execute(
            select(TankSettings).where(TankSettings.tank_id == existing.tank_id)
        ).scalar_one_or_none()

        return TankRegisterResponse(
            message="Tank re-registered and token refreshed 🔄",
            tank_id=str(existing.tank_id),
            access_token=new_token,
            firmware_version=existing.firmware_version,
            light_on=existing_settings.light_on if existing_settings else None, # Safely get light_on
            light_off=existing_settings.light_off if existing_settings else None, # Safely get light_off
            is_schedule_enabled=existing_settings.is_schedule_enabled if existing_settings else False, # Safely get schedule status
        )

    # Business Rule: Register a new tank if no existing tank is found with the given name.
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

    # Business Rule: Create default settings for the newly registered tank.
    # Times are already IST-aware due to Pydantic validation and conversion.
    tank_settings = TankSettings(
        tank_id=new_tank.tank_id,
        light_on=request.light_on,
        light_off=request.light_off,
    )
    db.add(tank_settings)
    db.commit()
    db.refresh(tank_settings)

    # Notify via Discord for new registration. Essential for operational awareness.
    extra_fields = {
        "Tank ID":           str(new_tank.tank_id),
        "Tank Name":         new_tank.tank_name,
        "Location":          new_tank.location or "—",
        "Firmware Version":  new_tank.firmware_version or "—",
        "Light On (IST)":    tank_settings.light_on.strftime("%H:%M"),
        "Light Off (IST)":   tank_settings.light_off.strftime("%H:%M"),
        "Schedule Enabled":  tank_settings.is_schedule_enabled,
    }
    await send_discord_embed(
        status="new_registration",
        tank_name=new_tank.tank_name,
        extra_fields=extra_fields
    )

    # Return the successful registration response.
    return TankRegisterResponse(
        message="Tank registered successfully ✅",
        tank_id=str(new_tank.tank_id),
        access_token=token,
        firmware_version=new_tank.firmware_version,
        light_on=tank_settings.light_on,
        light_off=tank_settings.light_off,
        is_schedule_enabled=tank_settings.is_schedule_enabled,
    )

def get_tank_by_id(db: Session, tank_id: uuid.UUID) -> Tank | None:
    """
    Retrieves a tank by its ID.
    """
    return db.scalars(select(Tank).where(Tank.tank_id == tank_id)).first()
