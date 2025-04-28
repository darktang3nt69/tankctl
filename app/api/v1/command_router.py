from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_tank
from app.schemas.command import CommandIssueRequest, CommandIssueResponse, CommandAcknowledgeRequest
from app.services.command_service import (
    issue_command,
    get_pending_command_for_tank,
    acknowledge_command,
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
    Admins can issue a command (feed_now, light_on, light_off) to a specific tank.
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
    Node can fetch its pending command.
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
    request: CommandAcknowledgeRequest,
    db: Session = Depends(get_db),
    tank_id: UUID = Depends(get_current_tank),
    background_tasks: BackgroundTasks = Depends(),
):
    """
    Node sends acknowledgment if it executed command successfully or failed.
    """
    try:
        # Update DB
        acknowledge_command(db, tank_id, request)

        # Fetch the tank and command info to send notification
        tank = db.query(Tank).filter(Tank.tank_id == tank_id).first()
        command = db.query(TankCommand).filter(TankCommand.command_id == request.command_id).first()

        if tank and command:
            # 🚀 Send notification in background
            background_tasks.add_task(
                NotificationService.send_command_acknowledgement_notification,
                tank_name=tank.tank_name,
                command_payload=command.command_payload,
                success=request.success,
            )

        return {"message": "Command acknowledged successfully"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
