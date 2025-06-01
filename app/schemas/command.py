# app/schemas/command.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class CommandIssueRequest(BaseModel):
    command_payload: str = Field(..., description="Command to be executed by the tank (e.g., 'feed_now' for feeding, 'light_on' for turning lights on)")

class CommandIssueResponse(BaseModel):
    command_id: UUID = Field(..., description="Unique identifier for the issued command")
    tank_id: UUID = Field(..., description="Identifier of the tank that will execute the command")
    command_payload: str = Field(..., description="The command that was issued to the tank")
    status: str = Field(..., description="Current status of the command (e.g., 'pending', 'acknowledged', 'completed')")
    retries: int = Field(..., description="Number of times the command has been retried")
    next_retry_at: datetime = Field(..., description="Timestamp when the command will be retried if not acknowledged")
    created_at: datetime = Field(..., description="Timestamp when the command was created")

class CommandAcknowledgeRequest(BaseModel):
    command_id: UUID = Field(..., description="Unique identifier of the command to acknowledge")
    success: bool = Field(..., description="Whether the command was successfully executed (true) or failed (false)")
