"""
# Command Router

This module provides API endpoints for issuing commands to tanks and for tanks to fetch and acknowledge commands.

## Endpoints
- **POST /tank/{tank_id}/command**: Admin issues a command to a tank.
- **GET /tank/command**: Tank fetches its pending command.
- **POST /tank/command/ack**: Tank acknowledges command execution.
- **GET /tank/{tank_id}/commands/history**: Retrieve command history for a tank.

Purpose: Facilitate command-and-control operations between the server and tank nodes.
"""
# app/api/v1/command_router.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.api.deps import get_db, get_current_tank
from app.schemas.command import CommandAcknowledgeRequest, CommandCreate, CommandResponse, CommandType
from app.services.command_service import (
    issue_command,
    get_pending_command_for_tank,
    acknowledge_command,
    get_command_history_for_tank,
    get_command_by_id,
    get_commands
)
from app.services.notification_service import NotificationService
from app.models.tank import Tank
from app.models.tank_command import TankCommand
from app.services.tank_service import get_tank_by_id
from app.api.utils.responses import create_success_response, create_error_response, create_paginated_response

router = APIRouter()

# 🛠 Admin Route: Issue a command to a tank
@router.post("/commands", response_model=CommandResponse, status_code=status.HTTP_202_ACCEPTED)
async def issue_command(
    command: CommandCreate,
    db: Session = Depends(get_db),
):
    """
    Issue a command to a tank.
    
    Available command types:
    - light_on: Turn on the tank light
    - light_off: Turn off the tank light
    - set_temperature: Set the target temperature (requires "temperature" parameter)
    - feed: Trigger feeding mechanism
    
    Parameters for set_temperature:
    - temperature: Target temperature in Celsius (0-40)
    
    Returns:
        CommandResponse: Command details including ID and status
    
    Raises:
        400: Invalid command parameters or tank offline
        404: Tank not found
        500: Server error
    """
    try:
        # Check if tank exists and is online
        tank = get_tank_by_id(db, UUID(command.tank_id))
        
        if not tank:
            return create_error_response(
                code="TANK_NOT_FOUND",
                message=f"Tank with ID {command.tank_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not tank.is_online:
            return create_error_response(
                code="TANK_OFFLINE",
                message=f"Tank with ID {command.tank_id} is offline",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Create the command using existing service
        command_result = issue_command(db, UUID(command.tank_id), command.command_type.value, command.parameters)
        
        # Enhance the response with additional information
        enhanced_response = {
            "command_id": command_result.command_id,
            "status": command_result.status,  # Initial status from service
            "timestamp": command_result.created_at.isoformat(),
            "tank_id": command_result.tank_id,
            "command_type": command_result.command_payload.get("command_type"), # Extract command_type from payload
            "parameters": command_result.command_payload.get("parameters"), # Extract parameters from payload
            "estimated_execution": datetime.utcnow().isoformat()  # Estimate when command will execute
        }
        
        return create_success_response(
            data=enhanced_response,
            status_code=status.HTTP_202_ACCEPTED
        )
    except ValueError as e:
        return create_error_response(
            code="INVALID_COMMAND",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(f"DEBUG: Unhandled exception in issue_command: {e}") # Added for debugging
        raise e # Temporarily re-raise for full traceback
        # return create_error_response(
        #     code="COMMAND_ERROR",
        #     message="Failed to issue command",
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        # )


# 🛠 Node Route: Tank fetches its pending command
@router.get("/tank/command")
def get_my_command(
    db: Session = Depends(get_db),
    tank_id: UUID = Depends(get_current_tank),
):
    """
    ## Purpose
    Tank node fetches its pending command from the server.

    ## Inputs
    - **db** (`Session`): SQLAlchemy database session (injected).
    - **tank_id** (`UUID`): The unique identifier of the tank (injected).

    ## Logic
    1. Call `get_pending_command_for_tank` to retrieve the next command for the tank.
    2. Return command details if found, or a message if none are pending.

    ## Outputs
    - **Success:**
        - `command_id` (str): ID of the pending command.
        - `command_payload` (str): The command to execute.
    - **No Pending Command:**
        - `message` (str): Informational message.
    """
    command = get_pending_command_for_tank(db, tank_id)
    if not command:
        return {"message": "No pending command"}

    return {
        "command_id": str(command.command_id),
        "command_payload": command.command_payload,
    }


# 🛠 Admin Route: Get command status by ID
@router.get("/commands/{command_id}", response_model=CommandResponse)
async def get_command_status(
    command_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        # Get command status from database
        command = get_command_by_id(db, command_id)
        
        if not command:
            return create_error_response(
                code="COMMAND_NOT_FOUND",
                message=f"Command with ID {command_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Format the response
        command_status = {
            "command_id": command.command_id,
            "status": command.status,
            "timestamp": command.created_at.isoformat(),
            "tank_id": command.tank_id,
            "command_type": command.command_payload.get("command_type"), # Extract command_type from payload
            "parameters": command.command_payload.get("parameters"), # Extract parameters from payload
            "last_updated": command.updated_at.isoformat(),
            "completion_time": command.completed_at.isoformat() if command.completed_at else None,
            "result": command.result
        }
        
        return create_success_response(data=command_status)
    except Exception as e:
        return create_error_response(
            code="STATUS_ERROR",
            message="Failed to retrieve command status",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# 🛠 Node Route: Tank acknowledges command execution
@router.post("/tank/command/ack")
def ack_my_command(
    background_tasks: BackgroundTasks,  # ✅ First
    request: CommandAcknowledgeRequest,
    db: Session = Depends(get_db),
    tank_id: UUID = Depends(get_current_tank),
):
    """
    ## Purpose
    Tank node acknowledges the execution result of a command.

    ## Inputs
    - **background_tasks** (`BackgroundTasks`): For adding notification tasks.
    - **request** (`CommandAcknowledgeRequest`): Contains command ID and success status.
    - **db** (`Session`): SQLAlchemy database session (injected).
    - **tank_id** (`UUID`): The unique identifier of the tank (injected).

    ## Logic
    1. Call `acknowledge_command` to update the command status in the database.
    2. Add a background task to send notifications if necessary.

    ## Outputs
    - **Success (200):** `message` (str): Confirmation message.
    - **Error (404):** If the command is not found.
    """
    try:
        acknowledge_command(db, tank_id, request)
        return {"message": "Command acknowledged successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/commands", response_model=list[CommandResponse])
async def get_command_history(
    tank_id: Optional[str] = None,
    status: Optional[str] = None,
    command_type: Optional[CommandType] = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
):
    try:
        # Get commands with filtering
        commands, total = get_commands(
            db=db,
            tank_id=UUID(tank_id) if tank_id else None,
            status=status,
            command_type=command_type.value if command_type else None,
            skip=(page - 1) * size,
            limit=size
        )
        
        # Format the response
        command_list = [
            {
                "command_id": cmd.command_id,
                "status": cmd.status,
                "timestamp": cmd.created_at.isoformat(),
                "tank_id": cmd.tank_id,
                "command_type": cmd.command_payload.get("command_type"), # Extract command_type from payload
                "parameters": cmd.command_payload.get("parameters"), # Extract parameters from payload
                "last_updated": cmd.updated_at.isoformat(),
                "completion_time": cmd.completed_at.isoformat() if cmd.completed_at else None,
                "result": cmd.result
            }
            for cmd in commands
        ]
        
        return create_paginated_response(
            data=command_list,
            total=total,
            page=page,
            size=size
        )
    except Exception as e:
        return create_error_response(
            code="HISTORY_ERROR",
            message="Failed to retrieve command history",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
