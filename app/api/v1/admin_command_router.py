# app/api/v1/admin_command_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, verify_admin_api_key
from app.services.admin_command_service import issue_admin_command
from app.schemas.admin_command import AdminSendCommandRequest
from uuid import UUID

router = APIRouter()

@router.post("/admin/send_command_to_tank", status_code=201)
def send_command_to_tank(
    request: AdminSendCommandRequest,  # ✅ Accept JSON body here
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key),
):
    """
    Admin can manually send a command to a tank using API Key auth.
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
