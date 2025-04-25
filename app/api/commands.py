from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Tank, Command
from app.core.auth import get_current_tank
from app.tasks.commands import schedule_command
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC

router = APIRouter()

class CommandRequest(BaseModel):
    command: str
    parameters: Optional[dict] = None

class CommandResponse(BaseModel):
    id: int
    tank_id: int
    command: str
    parameters: Optional[dict]
    created_at: datetime
    acknowledged: bool
    ack_time: Optional[datetime]

class CommandCreate(BaseModel):
    command: str
    parameters: Optional[Dict[str, Any]] = None

@router.post("/commands")
def create_command(
    command: CommandCreate,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    command_id = schedule_command.delay(
        tank_id=tank.id,
        command=command.command,
        parameters=command.parameters
    )
    return {"message": "Command scheduled", "command_id": command_id}

@router.get("/commands/{tank_id}", response_model=List[CommandResponse])
def get_commands(
    tank_id: int,
    unacknowledged_only: bool = True,
    limit: Optional[int] = 100,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    # Verify tank_id matches authenticated tank
    if tank.id != tank_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tank's commands"
        )
    
    query = db.query(Command).filter(Command.tank_id == tank_id)
    
    if unacknowledged_only:
        query = query.filter(Command.acknowledged == False)
    
    commands = query.order_by(Command.created_at.desc()).limit(limit).all()
    return commands

@router.post("/commands/{command_id}/ack")
def acknowledge_command(
    command_id: int,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
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
    
    command.acknowledged = True
    db.commit()
    return {"message": "Command acknowledged"}