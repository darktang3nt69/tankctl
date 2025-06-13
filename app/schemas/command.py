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
from typing import Optional, Dict, Any # Import Optional for optional fields
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

class CommandAcknowledgeRequest(BaseModel):
    command_id: UUID = Field(..., description="Unique identifier of the command to acknowledge")
    success: bool = Field(..., description="Whether the command was successfully executed (true) or failed (false)")

class CommandType(str, Enum):
    LIGHT_ON = "light_on"
    LIGHT_OFF = "light_off"
    SET_TEMPERATURE = "set_temperature"
    FEED = "feed"
    # Add other command types as needed

class CommandCreate(BaseModel):
    tank_id: str = Field(..., description="ID of the tank to command")
    command_type: CommandType = Field(..., description="Type of command to issue")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Command parameters")
    
    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v, info):
        command_type = info.data.get("command_type")
        
        # Validate parameters based on command type
        if command_type == CommandType.SET_TEMPERATURE:
            if "temperature" not in v:
                raise ValueError("Temperature parameter is required for SET_TEMPERATURE command")
            
            temp = v.get("temperature")
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 40:
                raise ValueError("Temperature must be a number between 0 and 40")
        
        # Add validation for other command types as needed
        
        return v

class CommandResponse(BaseModel):
    command_id: UUID
    status: str
    timestamp: datetime
    tank_id: UUID
    command_type: CommandType
    parameters: Dict[str, Any]
    last_updated: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    result: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.astimezone(IST).isoformat(timespec='microseconds')
        }
