"""
Command Routes - Command receiving and management endpoints.

POST /devices/{device_id}/commands - Send command to device
GET /devices/{device_id}/commands - Get command history
POST /devices/{device_id}/light - Set light state (convenience endpoint)
POST /devices/{device_id}/pump - Set pump state (convenience endpoint)
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from src.api.schemas import CommandRequest, CommandResponse
from src.infrastructure.db.database import db
from src.services.command_service import CommandService
from src.services.shadow_service import ShadowService
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/devices", tags=["commands"])


def get_db():
    """Dependency: Get database session."""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


@router.post("/{device_id}/commands", response_model=CommandResponse, status_code=202)
def send_command(
    device_id: str,
    request: CommandRequest,
    session: Session = Depends(get_db)
):
    """
    Send a command to a device.
    
    Args:
        device_id: Target device ID
        request: Command request with command name and optional value
    
    Returns:
        Command metadata (accepted for processing)
    """
    try:
        logger.info(
            "command_received",
            device_id=device_id,
            command=request.command
        )
        
        command_service = CommandService(session)
        command = command_service.send_command(
            device_id=device_id,
            command=request.command,
            value=request.value,
        )
        
        logger.info(
            "command_sent",
            device_id=device_id,
            command=request.command,
            version=command.version,
        )
        
        return CommandResponse(
            command_id=command.device_id,
            device_id=command.device_id,
            command=command.command,
            value=command.value,
            version=command.version,
            status=command.status,
        )
        
    except Exception as e:
        logger.error(
            "send_command_error",
            device_id=device_id,
            command=request.command,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to send command")


@router.get("/{device_id}/commands", response_model=dict)
def get_command_history(
    device_id: str,
    limit: int = 20,
    session: Session = Depends(get_db)
):
    """
    Get command history for device.
    
    Args:
        device_id: Device ID
        limit: Maximum number of commands (default 20)
    
    Returns:
        List of recent commands
    """
    try:
        logger.debug("getting_command_history", device_id=device_id, limit=limit)
        
        command_service = CommandService(session)
        commands = command_service.get_command_history(device_id, limit=limit)
        
        command_list = [
            CommandResponse(
                command_id=c.device_id,
                device_id=c.device_id,
                command=c.command,
                value=c.value,
                version=c.version,
                status=c.status,
            )
            for c in commands
        ]
        
        return {
            "count": len(command_list),
            "commands": command_list,
        }
        
    except Exception as e:
        logger.error("get_command_history_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{device_id}/light", response_model=CommandResponse, status_code=202)
def set_light(
    device_id: str,
    request: dict,
    session: Session = Depends(get_db)
):
    """
    Set light state (convenience endpoint).
    
    Request body:
    {
        "state": "on"  or "off"
    }
    
    Args:
        device_id: Target device ID
        request: Light state request
    
    Returns:
        Command metadata
    """
    try:
        if "state" not in request:
            raise HTTPException(status_code=400, detail="Request must include 'state' field")
        
        state = request["state"]
        if state not in ["on", "off"]:
            raise HTTPException(status_code=400, detail="State must be 'on' or 'off'")
        
        logger.info("setting_light", device_id=device_id, state=state)
        
        # Update shadow desired state
        shadow_service = ShadowService(session)
        shadow = shadow_service.set_desired_state(device_id, {"light": state})
        
        if not shadow:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Send command
        command_service = CommandService(session)
        command = command_service.send_command(
            device_id=device_id,
            command="set_light",
            value=state,
        )
        
        logger.info("light_command_sent", device_id=device_id, state=state)
        
        return CommandResponse(
            command_id=command.device_id,
            device_id=command.device_id,
            command=command.command,
            value=command.value,
            version=command.version,
            status=command.status,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("set_light_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to set light")


@router.post("/{device_id}/pump", response_model=CommandResponse, status_code=202)
def set_pump(
    device_id: str,
    request: dict,
    session: Session = Depends(get_db)
):
    """
    Set pump state (convenience endpoint).
    
    Request body:
    {
        "state": "on"  or "off"
    }
    
    Args:
        device_id: Target device ID
        request: Pump state request
    
    Returns:
        Command metadata
    """
    try:
        if "state" not in request:
            raise HTTPException(status_code=400, detail="Request must include 'state' field")
        
        state = request["state"]
        if state not in ["on", "off"]:
            raise HTTPException(status_code=400, detail="State must be 'on' or 'off'")
        
        logger.info("setting_pump", device_id=device_id, state=state)
        
        # Update shadow desired state
        shadow_service = ShadowService(session)
        shadow = shadow_service.set_desired_state(device_id, {"pump": state})
        
        if not shadow:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Send command
        command_service = CommandService(session)
        command = command_service.send_command(
            device_id=device_id,
            command="set_pump",
            value=state,
        )
        
        logger.info("pump_command_sent", device_id=device_id, state=state)
        
        return CommandResponse(
            command_id=command.device_id,
            device_id=command.device_id,
            command=command.command,
            value=command.value,
            version=command.version,
            status=command.status,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("set_pump_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to set pump")
