"""
# Override Router

This module provides API endpoints for administrators to manually override tank settings, such as turning lights ON/OFF.

## Endpoints
- **POST /tank/override**: Manually override tank settings (admin only, API key required).

Purpose: Allow authorized administrators to directly control tank hardware for maintenance or emergency intervention.
"""
# app/api/v1/override_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, verify_admin_api_key
from app.models.tank_settings import TankSettings
from app.schemas.tank_settings import TankSettingsResponse, TankOverrideRequest
from app.services.tank_settings_service import manual_override_command
from app.core.exceptions import TankNotFoundError

router = APIRouter(
    prefix="/tank/override",
    tags=["manual override"],
)

@router.post(
    "",
    response_model=TankSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="(Admin) Manually override lights ON/OFF for a tank",
    dependencies=[Depends(verify_admin_api_key)],  # require x-api-key
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "default": {
                            "summary": "Override lights ON",
                            "value": {
                                "tank_id": "66666666-6666-6666-6666-666666666666",
                                "override_command": "light_on"
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
                                "summary": "Override success",
                                "value": {
                                    "tank_id": "66666666-6666-6666-6666-666666666666",
                                    "light_on": "10:00",
                                    "light_off": "16:00",
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
                "description": "Tank settings not found.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "examples": {
                            "not_found": {
                                "summary": "Tank settings not found",
                                "value": {"detail": "Tank settings not found"}
                            }
                        }
                    }
                }
            }
        }
    }
)
def override_tank(
    req: TankOverrideRequest,
    db: Session = Depends(get_db),
):
    """
    ## Purpose
    Admin manually overrides tank settings (e.g., lights ON/OFF) for a specific tank.

    ## Inputs
    - **req** (`TankOverrideRequest`): Contains the tank ID and override command ('light_on' or 'light_off').
    - **db** (`Session`): SQLAlchemy database session (injected).

    ## Logic
    1. Retrieve the tank's settings from the database.
    2. If settings are not found, raise HTTP 404.
    3. Apply the manual override using `manual_override_command`.
    4. Return the updated settings record.

    ## Outputs
    - **Success (200):** `TankSettingsResponse` with updated settings.
    - **Error (404):** `detail` (str): Error message if tank settings are not found.
    """
    # 1) ensure the tank has settings
    settings = db.get(TankSettings, req.tank_id)
    if not settings:
        raise TankNotFoundError(detail="Tank settings not found")

    # 2) apply manual override (payload.override_command is 'light_on' or 'light_off')
    updated = manual_override_command(db, req)

    # 3) return the updated settings record
    return updated
