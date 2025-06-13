"""
# Settings Router

This module provides API endpoints for administrators to manage tank lighting settings, schedules, and manual overrides.

## Endpoints
- **GET /tank/settings**: Fetch a tank's lighting settings (admin only, API key required).
- **PUT /tank/settings**: Update a tank's lighting schedule (admin only, API key required).
- **POST /tank/settings/override**: Manually override tank lights ON/OFF (admin only, API key required).
- **POST /tank/settings/override/clear**: Clear manual override and resume schedule (admin only, API key required).

Purpose: Enable fine-grained control and monitoring of tank lighting schedules and manual interventions for maintenance or emergencies.
"""
# app/api/v1/settings_router.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.models.tank import Tank
from app.schemas.tank_settings import (
    TankSettingsResponse,
    TankSettingsUpdateRequest,
    TankOverrideRequest,
)
from app.services.tank_settings_service import (
    get_or_create_settings,
    update_tank_settings,
    manual_override_command,
)
from app.utils.discord import send_discord_embed
from app.core.exceptions import TankNotFoundError, InternalServerError

router = APIRouter(
    prefix="/tank/settings",
    tags=["tank settings"],
)


def _ensure_tank_exists(db: Session, tank_id: str):
    """
    ## Purpose
    Raise HTTP 404 if no Tank row with this ID exists.

    ## Inputs
    - **db** (`Session`): SQLAlchemy database session.
    - **tank_id** (`str`): The unique identifier of the tank.

    ## Logic
    1. Query the database for the tank by ID.
    2. If not found, raise HTTP 404.

    ## Outputs
    - None (raises exception on error).
    """
    if not db.get(Tank, tank_id):
        raise TankNotFoundError(detail=f"Tank '{tank_id}' not found.")


@router.get(
    "",
    response_model=TankSettingsResponse,
    summary="(Admin) Fetch a tank's lighting settings",
    openapi_extra={
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "examples": {
                            "success": {
                                "summary": "Successfully fetched settings",
                                "value": {
                                    "tank_id": "77777777-7777-7777-7777-777777777777",
                                    "light_on": "09:00",
                                    "light_off": "17:00",
                                    "is_schedule_enabled": True,
                                    "schedule_paused_until": None,
                                    "last_schedule_check_on": None,
                                    "last_schedule_check_off": None
                                }
                            }
                        }
                    }
                }
            },
            "404": {
                "description": "Tank not found.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "examples": {
                            "not_found": {
                                "summary": "Tank not found",
                                "value": {"detail": "Tank not found"}
                            }
                        }
                    }
                }
            }
        }
    }
)
def read_settings(
    *,
    tank_id: UUID = Query(..., description="UUID of the tank"),
    db: Session = Depends(get_db),
):
    """
    ## Purpose
    Fetch the lighting settings for a specific tank.

    ## Inputs
    - **tank_id** (`UUID`): The unique identifier of the tank.
    - **db** (`Session`): SQLAlchemy database session (injected).

    ## Logic
    1. Ensure the tank exists.
    2. Retrieve or create the tank's settings.

    ## Outputs
    - **Success:** `TankSettingsResponse` with current settings.
    - **Error (404):** If tank not found.
    """
    _ensure_tank_exists(db, str(tank_id))
    return get_or_create_settings(db, str(tank_id))


@router.put(
    "",
    response_model=TankSettingsResponse,
    summary="(Admin) Update a tank's lighting schedule",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "default": {
                            "summary": "Update lighting schedule",
                            "value": {
                                "tank_id": "77777777-7777-7777-7777-777777777777",
                                "light_on": "09:00",
                                "light_off": "17:00",
                                "is_schedule_enabled": True
                            }
                        }
                    }
                }
            }
        },
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "examples": {
                            "success": {
                                "summary": "Update success",
                                "value": {
                                    "tank_id": "77777777-7777-7777-7777-777777777777",
                                    "light_on": "09:00",
                                    "light_off": "17:00",
                                    "is_schedule_enabled": True,
                                    "schedule_paused_until": "",
                                    "last_schedule_check_on": "",
                                    "last_schedule_check_off": ""
                                }
                            }
                        }
                    }
                }
            },
            "404": {
                "description": "Tank not found.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "examples": {
                            "not_found": {
                                "summary": "Tank not found",
                                "value": {"detail": "Tank not found"}
                            }
                        }
                    }
                }
            },
            "500": {
                "description": "Internal server error.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "examples": {
                            "server_error": {
                                "summary": "Internal server error",
                                "value": {"detail": "Internal server error"}
                            }
                        }
                    }
                }
            }
        }
    }
)
def put_settings(
    *,
    payload: TankSettingsUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    ## Purpose
    Update the lighting schedule for a specific tank.

    ## Inputs
    - **payload** (`TankSettingsUpdateRequest`): Contains tank ID and new schedule.
    - **db** (`Session`): SQLAlchemy database session (injected).

    ## Logic
    1. Ensure the tank exists.
    2. Update the tank's settings using the provided payload.
    3. Handle and report any errors.

    ## Outputs
    - **Success:** `TankSettingsResponse` with updated settings.
    - **Error (404/500):** If tank not found or update fails.
    """
    _ensure_tank_exists(db, str(payload.tank_id))
    try:
        # update_tank_settings now also clears any outstanding pause
        return update_tank_settings(db, str(payload.tank_id), payload)
    except Exception as e:
        raise InternalServerError(detail=str(e))


@router.post(
    "/override",
    response_model=TankSettingsResponse,
    summary="(Admin) Manually override lights ON or OFF",
)
def post_manual_override(
    *,
    payload: TankOverrideRequest,
    db: Session = Depends(get_db),
):
    """
    ## Purpose
    Manually override tank lights ON or OFF and pause automated scheduling.

    ## Inputs
    - **payload** (`TankOverrideRequest`): Contains tank ID and override command ('on' or 'off').
    - **db** (`Session`): SQLAlchemy database session (injected).

    ## Logic
    1. Ensure the tank exists.
    2. Apply the manual override using the provided payload.
    3. Pause automated scheduling until the next schedule edge.

    ## Outputs
    - **Success:** `TankSettingsResponse` with updated settings.
    - **Error (404):** If tank not found.
    """
    tank_id = str(payload.tank_id)
    _ensure_tank_exists(db, tank_id)
    return manual_override_command(db, payload)


@router.post(
    "/override/clear",
    response_model=TankSettingsResponse,
    summary="(Admin) Clear any manual lighting pause and resume schedule immediately",
)
def clear_manual_override(
    *,
    tank_id: UUID = Query(..., description="UUID of the tank"),
    db: Session = Depends(get_db),
):
    """
    ## Purpose
    Clear any outstanding manual lighting pause and immediately resume normal scheduling.

    ## Inputs
    - **tank_id** (`UUID`): The unique identifier of the tank.
    - **db** (`Session`): SQLAlchemy database session (injected).

    ## Logic
    1. Ensure the tank exists.
    2. Retrieve the tank's settings.
    3. If a manual pause is active (`schedule_paused_until` is set), clear it.
    4. Reset `last_schedule_check_on` and `last_schedule_check_off` to ensure the schedule runs immediately.
    5. Commit changes to the database.

    ## Outputs
    - **Success (200):** `TankSettingsResponse` with the updated settings.
    - **Error (404):** If the tank is not found.
    """
    tid = str(tank_id)
    _ensure_tank_exists(db, tid)

    settings = get_or_create_settings(db, tid)

    # nothing to do?
    if settings.schedule_paused_until is None:
        return settings

    # clear the pause and today's markers
    settings.schedule_paused_until   = None
    settings.last_schedule_check_on  = None
    settings.last_schedule_check_off = None

    db.add(settings)
    db.commit()
    db.refresh(settings)

    send_discord_embed(
        status="override_cleared",
        tank_name=settings.tank.tank_name,
        command_payload="Pause cleared via API"
    )

    return settings
