from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

class CommandAck(BaseModel):
    command_id: int
    success: bool = True

@router.post("/commands", response_model=CommandResponse)
async def create_command(
    command: CommandCreate,
    tank: Tank = Depends(get_current_tank),
    db: AsyncSession = Depends(get_db)
):
    """
    Create and schedule a new command for execution.
    
    The command will be queued and processed asynchronously. The response includes
    the command details and initial status. Use the command ID to check status
    and acknowledge completion.
    """
    logger.info(f"Creating command for tank {tank.id}: {command.command}")
    try:
        # Create the command in the database first
        db_command = Command(
            tank_id=tank.id,
            command=command.command,
            parameters=command.parameters,
            timeout=command.timeout
        )
        db.add(db_command)
        await db.commit()
        await db.refresh(db_command)
        
        # Schedule the command for processing
        schedule_command.delay(
            tank_id=tank.id,
            command=command.command,
            parameters=command.parameters
        )
        
        return db_command
        
    except Exception as e:
        logger.error(f"Error scheduling command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling command: {str(e)}"
        )

@router.get("/commands", response_model=List[CommandResponse])
async def get_commands(
    status: Optional[CommandStatus] = None,
    unacknowledged_only: bool = Query(False, description="Only return unacknowledged commands"),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    tank: Tank = Depends(get_current_tank),
    db: AsyncSession = Depends(get_db)
):
    """
    Get commands for the authenticated tank with optional filtering by status and acknowledgment.
    """
    query = select(Command).where(Command.tank_id == tank.id)
    
    if status:
        query = query.where(Command.status == status)
    
    if unacknowledged_only:
        query = query.where(Command.acknowledged == False)
    
    query = query.order_by(Command.created_at.desc()).limit(limit)
    result = await db.execute(query)
    commands = result.scalars().all()
    return commands

@router.get("/commands/{command_id}", response_model=CommandResponse)
async def get_command(
    command_id: int,
    tank: Tank = Depends(get_current_tank),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific command.
    """
    result = await db.execute(
        select(Command).where(
            Command.id == command_id,
            Command.tank_id == tank.id
        )
    )
    command = result.scalar_one_or_none()
    
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )
    
    return command

@router.post("/commands/ack", response_model=CommandResponse)
async def acknowledge_command(
    ack: CommandAck,
    tank: Tank = Depends(get_current_tank),
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge completion of a command.
    
    This endpoint should be called by the tank when it has completed
    executing the command. The success parameter indicates whether
    the command executed successfully or failed.
    """
    result = await db.execute(
        select(Command).where(Command.id == ack.command_id)
    )
    command = result.scalar_one_or_none()
    
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
    command.status = CommandStatus.COMPLETED if ack.success else CommandStatus.FAILED
    await db.commit()
    await db.refresh(command)

    # Send Discord notification
    from app.tasks.notifications import send_discord_notification
    send_discord_notification.delay(
        f"✅ Command {command.command} completed successfully" if ack.success else
        f"❌ Command {command.command} failed to execute",
        tank_id=command.tank_id
    )
    
    return command

@router.post("/commands/{command_id}/retry")
async def retry_command(
    command_id: int,
    tank: Tank = Depends(get_current_tank),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually retry a failed or timed out command.
    """
    result = await db.execute(
        select(Command).where(Command.id == command_id)
    )
    command = result.scalar_one_or_none()
    
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
    
    if command.status not in [CommandStatus.FAILED, CommandStatus.TIMEOUT]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed or timed out commands"
        )
    
    # Reset command status and increment retry count
    command.status = CommandStatus.PENDING
    command.retry_count += 1
    command.last_retry = datetime.now(UTC)
    await db.commit()
    await db.refresh(command)
    
    # Queue command for processing
    await process_command.delay(command.id)
    
    return {"message": "Command queued for retry"}