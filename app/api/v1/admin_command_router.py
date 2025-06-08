"""
# Admin Command Router

This module provides API endpoints for administrators to manually send commands to tanks.

## Endpoints
- **POST /admin/send_command_to_tank**: Send a command to a tank (admin only, API key required).

Purpose: Facilitate manual control and intervention for tank operations by authorized administrators.
"""
# app/api/v1/admin_command_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, verify_admin_api_key
from app.services.admin_command_service import issue_admin_command
from app.schemas.admin_command import AdminSendCommandRequest
from uuid import UUID

router = APIRouter()

@router.post("/admin/send_command_to_tank", status_code=201,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "default": {
                            "summary": "Send feed_now command",
                            "value": {
                                "tank_id": "11111111-1111-1111-1111-111111111111",
                                "command_payload": "feed_now"
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
                                "summary": "Command created",
                                "value": {
                                    "message": "Command created successfully",
                                    "command_id": "22222222-2222-2222-2222-222222222222",
                                    "tank_id": "11111111-1111-1111-1111-111111111111",
                                    "command_payload": "feed_now",
                                    "created_at": "2024-06-01T12:00:00+05:30"
                                }
                            }
                        }
                    }
                }
            },
            "404": {
                "description": "Tank or command not found.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "examples": {
                            "not_found": {
                                "summary": "Tank or command not found",
                                "value": {"detail": "Tank or command not found"}
                            }
                        }
                    }
                }
            }
        }
    }
)
def send_command_to_tank(
    request: AdminSendCommandRequest,  # ✅ Accept JSON body here
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key),
):
    """
    ## Purpose
    Manually send a command to a tank using admin API Key authentication.

    ## Inputs
    - **request** (`AdminSendCommandRequest`):
        - `tank_id` (UUID): The unique identifier of the target tank.
        - `command_payload` (str): The command to send (e.g., 'feed_now', 'light_on', 'light_off').
    - **db** (`Session`): SQLAlchemy database session (injected).
    - **_** (`str`): API key verification (injected, unused).

    ## Logic
    1. Verify admin API key via dependency injection.
    2. Call `issue_admin_command` to create and store the command for the specified tank.
    3. Return a success message and command details if successful.
    4. Raise HTTP 404 if the tank or command is invalid.

    ## Outputs
    - **Success (201):**
        - `message` (str): Confirmation message.
        - `command_id` (str): ID of the created command.
        - `tank_id` (str): ID of the target tank.
        - `command_payload` (str): The command sent.
        - `created_at` (datetime): Timestamp of command creation.
    - **Error (404):**
        - `detail` (str): Error message if the tank or command is not found.
    """
    try:
        command = issue_admin_command(db, request.tank_id, request.command_payload)
        return {
            "message": "Command created successfully",
            "command_id": str(command.command_id),
            "tank_id": str(command.tank_id),
            "command_payload": command.command_payload,
            "created_at": command.created_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
