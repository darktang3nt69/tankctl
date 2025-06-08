"""
# Register Router

This module provides API endpoints for registering new tank nodes with the system.

## Endpoints
- **POST /tank/register**: Register a new tank node and receive a JWT token.

Purpose: Allow new tank nodes to securely join the system and receive authentication credentials.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.tank import TankRegisterRequest, TankRegisterResponse
from app.services.tank_service import register_tank
from app.api.deps import get_db
from app.core.exceptions import AuthenticationError

router = APIRouter()

@router.post(
    "/tank/register",
    response_model=TankRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new tank node",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "default": {
                            "summary": "Register tank",
                            "value": {
                                "auth_key": "my-secret-key",
                                "tank_name": "Tank 1",
                                "location": "Living Room",
                                "firmware_version": "1.0.0",
                                "light_on": "10:00",
                                "light_off": "16:00"
                            }
                        }
                    }
                }
            }
        },
        "responses": {
            "201": {
                "content": {
                    "application/json": {
                        "examples": {
                            "success": {
                                "summary": "Registration success",
                                "value": {
                                    "message": "Tank registered successfully",
                                    "tank_id": "55555555-5555-5555-5555-555555555555",
                                    "access_token": "jwt.token.here",
                                    "firmware_version": "1.0.0",
                                    "light_on": "10:00",
                                    "light_off": "16:00",
                                    "is_schedule_enabled": True
                                }
                            }
                        }
                    }
                }
            },
            "401": {
                "description": "Unauthorized - Registration failed or tank already exists with different auth key.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "examples": {
                            "registration_failed": {
                                "summary": "Registration Failed",
                                "value": {"detail": "Invalid authentication key"}
                            },
                            "tank_exists": {
                                "summary": "Tank Already Exists",
                                "value": {"detail": "Tank with this name already exists and auth key does not match"}
                            }
                        }
                    }
                }
            }
        }
    }
)
def tank_register(
    request: TankRegisterRequest,
    db: Session = Depends(get_db),
) -> TankRegisterResponse:
    """
    ## Purpose
    Register a new tank node and issue a JWT token for authentication.

    ## Inputs
    - **request** (`TankRegisterRequest`): Contains tank name and registration details.
    - **db** (`Session`): SQLAlchemy database session (injected).

    ## Logic
    1. Attempt to register the tank using `register_tank` service.
    2. If the tank is already registered (by name), return the existing JWT token.
    3. If registration fails, raise HTTP 401.

    ## Outputs
    - **Success (201):** `TankRegisterResponse` with JWT token and tank details.
    - **Error (401):** `detail` (str): Error message if registration fails.
    """
    try:
        return register_tank(db, request)
    except ValueError as e:
        raise AuthenticationError(detail=str(e))
