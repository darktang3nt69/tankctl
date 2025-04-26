from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Tank, Command, CommandStatus
from app.core.auth import get_current_tank
from app.tasks.commands import schedule_command, process_command
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class CommandRequest(BaseModel):
    command: str = Field(..., description="Command to execute")
    parameters: Optional[dict] = Field(None, description="Command parameters")
    timeout: Optional[int] = Field(300, description="Command timeout in seconds", ge=1, le=3600)

class CommandResponse(BaseModel):
    id: int
    tank_id: int
    command: str
    parameters: Optional[dict]
    created_at: datetime
    status: CommandStatus
    acknowledged: bool
    ack_time: Optional[datetime]
    retry_count: int
    last_retry: Optional[datetime]
    error_message: Optional[str]
    timeout: int

class CommandCreate(BaseModel):
    command: str = Field(..., description="Command to execute")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Command parameters")
    timeout: Optional[int] = Field(300, description="Command timeout in seconds", ge=1, le=3600)

@router.post("/commands", response_model=CommandResponse)
def create_command(
    command: CommandCreate,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    """
    Create and schedule a new command for execution.
    
    The command will be queued and processed asynchronously. The response includes
    the command details and initial status. Use the command ID to check status
    and acknowledge completion.
    """
    logger.info(f"Creating command for tank {tank.id}: {command.command}")
    try:
        command_id = schedule_command.delay(
            tank_id=tank.id,
            command=command.command,
            parameters=command.parameters
        )
        
        # Get the created command
        db_command = db.query(Command).filter(Command.id == command_id).first()
        if not db_command:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Command created but not found in database"
            )
            
        return db_command
        
    except Exception as e:
        logger.error(f"Error scheduling command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling command: {str(e)}"
        )

@router.get("/commands/{tank_id}", response_model=List[CommandResponse])
def get_commands(
    tank_id: int,
    status: Optional[CommandStatus] = None,
    unacknowledged_only: bool = Query(False, description="Only return unacknowledged commands"),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    """
    Get commands for a tank with optional filtering by status and acknowledgment.
    """
    # Verify tank_id matches authenticated tank
    if tank.id != tank_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tank's commands"
        )
    
    query = db.query(Command).filter(Command.tank_id == tank_id)
    
    if status:
        query = query.filter(Command.status == status)
    
    if unacknowledged_only:
        query = query.filter(Command.acknowledged == False)
    
    commands = query.order_by(Command.created_at.desc()).limit(limit).all()
    return commands

@router.get("/commands/{tank_id}/{command_id}", response_model=CommandResponse)
def get_command(
    tank_id: int,
    command_id: int,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific command.
    """
    # Verify tank_id matches authenticated tank
    if tank.id != tank_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tank's commands"
        )
    
    command = db.query(Command).filter(
        Command.id == command_id,
        Command.tank_id == tank_id
    ).first()
    
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )
    
    return command

@router.post("/commands/{command_id}/ack", response_model=CommandResponse)
def acknowledge_command(
    command_id: int,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    """
    Acknowledge completion of a command.
    
    This endpoint should be called by the tank when it has successfully
    executed the command. This will mark the command as completed and
    stop any pending retries.
    """
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )
    
    if command.tank_id != tank.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to acknowledge this command"
        )
    
    if command.acknowledged:
        return command  # Already acknowledged
    
    command.acknowledged = True
    command.ack_time = datetime.now(UTC)
    command.status = CommandStatus.COMPLETED
    db.commit()
    db.refresh(command)

    # Send Discord notification
    from app.tasks.notifications import send_discord_notification
    send_discord_notification.delay(
        f"✅ Command {command.command} for tank {tank.name} (ID: {tank.id}) "
        f"was successfully completed"
    )
    
    return command

@router.post("/commands/{command_id}/retry")
def retry_command(
    command_id: int,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    """
    Manually retry a failed or timed out command.
    """
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )
    
    if command.tank_id != tank.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to retry this command"
        )
    
    if command.status not in [CommandStatus.FAILED, CommandStatus.TIMED_OUT]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry command in status {command.status}"
        )
    
    # Reset command status and retry count
    command.status = CommandStatus.PENDING
    command.retry_count = 0
    command.error_message = None
    command.last_retry = None
    db.commit()
    
    # Start processing the command
    process_command.delay(command.id)
    
    return {"message": "Command scheduled for retry"}