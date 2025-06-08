"""
Command Schemas

This module defines the Pydantic schemas for command-related operations,
including models for issuing commands, command responses, and command acknowledgments.
It also defines an Enum for valid command payloads.
"""
# app/schemas/command.py

from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional # Import Optional for optional fields
from enum import Enum # Import Enum
from app.utils.timezone import IST # Import IST for serialization

# Define valid command payloads as an Enum
class CommandPayloadEnum(str, Enum):
    FEED_NOW = "feed_now"
    LIGHT_ON = "light_on"
    LIGHT_OFF = "light_off"
    RESTART = "restart"
    UPDATE_FIRMWARE = "update_firmware"
    RESET_SETTINGS = "reset_settings"

class CommandIssueRequest(BaseModel):
    command_payload: CommandPayloadEnum = Field(..., description="Command to be executed by the tank (e.g., 'feed_now' for feeding, 'light_on' for turning lights on)")

class CommandIssueResponse(BaseModel):
    command_id: UUID = Field(..., description="Unique identifier for the issued command")
    tank_id: UUID = Field(..., description="Identifier of the tank that will execute the command")
    command_payload: str = Field(..., description="The command that was issued to the tank")
    status: str = Field(..., description="Current status of the command (e.g., 'pending', 'acknowledged', 'completed')")
    retries: int = Field(..., description="Number of times the command has been retried")
    next_retry_at: datetime = Field(..., description="Timestamp when the command will be retried if not acknowledged")
    created_at: datetime = Field(..., description="Timestamp when the command was created")

    class Config:
        json_encoders = {
            datetime: lambda v: v.astimezone(IST).isoformat(timespec='microseconds')
        }

class CommandAcknowledgeRequest(BaseModel):
    command_id: UUID = Field(..., description="Unique identifier of the command to acknowledge")
    success: bool = Field(..., description="Whether the command was successfully executed (true) or failed (false)")
