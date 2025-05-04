# app/schemas/command.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class CommandIssueRequest(BaseModel):
    command_payload: str = Field(..., description="Command payload (e.g., 'feed_now')")

class CommandIssueResponse(BaseModel):
    command_id: UUID
    tank_id: UUID
    command_payload: str
    status: str
    retries: int
    next_retry_at: datetime
    created_at: datetime

class CommandAcknowledgeRequest(BaseModel):
    command_id: UUID
    success: bool
