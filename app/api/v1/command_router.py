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

from app.api.deps import get_db, get_current_tank
from app.schemas.command import CommandIssueRequest, CommandIssueResponse, CommandAcknowledgeRequest
from app.services.command_service import (
    issue_command,
    get_pending_command_for_tank,
    acknowledge_command,
    get_command_history_for_tank,
)
from app.services.notification_service import NotificationService
from app.models.tank import Tank
from app.models.tank_command import TankCommand

router = APIRouter()

# 🛠 Admin Route: Issue a command to a tank
@router.post("/tank/{tank_id}/command", response_model=CommandIssueResponse, status_code=201)
def create_command(
    tank_id: UUID,
    request: CommandIssueRequest,
    db: Session = Depends(get_db),
):
    """
    ## Purpose
    Admin issues a command (e.g., \'feed_now\', \'light_on\', \'light_off\') to a specific tank.

    ## Inputs
    - **tank_id** (`UUID`): The unique identifier of the target tank.
    - **request** (`CommandIssueRequest`): Contains the command payload.
    - **db** (`Session`): SQLAlchemy database session (injected).

    ## Logic
    1. Call `issue_command` to create and store the command for the specified tank.
    2. Return a structured response with command details if successful.
    3. Raise HTTP 400 if the command is invalid.

    ## Outputs
    - **Success (201):** `CommandIssueResponse` with command details.
    - **Error (400):** `detail` (str): Error message if the command is invalid.
    """
    try:
        command = issue_command(db, tank_id, request.command_payload)
        return CommandIssueResponse(
            command_id=command.command_id,
            tank_id=command.tank_id,
            command_payload=command.command_payload,
            status=command.status,
            retries=command.retries,
            next_retry_at=command.next_retry_at,
            created_at=command.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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


@router.get("/tank/{tank_id}/commands/history", response_model=list[CommandIssueResponse])
def get_tank_command_history(
    tank_id: UUID,
    db: Session = Depends(get_db),
    status: str | None = None,
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """
    ## Purpose
    Retrieve command history for a specific tank.

    ## Inputs
    - **tank_id** (`UUID`): The unique identifier of the tank.
    - **db** (`Session`): SQLAlchemy database session (injected).
    - **status** (`str`, optional): Filter commands by their status (e.g., 'pending', 'completed', 'failed').
    - **start_time** (`datetime`, optional): Filter commands created after this timestamp.
    - **end_time** (`datetime`, optional): Filter commands created before this timestamp.
    - **limit** (`int`, optional): Maximum number of commands to retrieve. Defaults to 100, max 500.

    ## Logic
    1. Call `get_command_history_for_tank` to fetch filtered command records.
    2. Return a list of `CommandIssueResponse` objects.

    ## Outputs
    - **Success (200):** List of `CommandIssueResponse` objects.
    """
    commands = get_command_history_for_tank(db, tank_id, status, start_time, end_time, limit)
    return [
        CommandIssueResponse(
            command_id=cmd.command_id,
            tank_id=cmd.tank_id,
            command_payload=cmd.command_payload,
            status=cmd.status,
            retries=cmd.retries,
            next_retry_at=cmd.next_retry_at,
            created_at=cmd.created_at,
        )
        for cmd in commands
    ]
