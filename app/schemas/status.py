"""
Status Schemas

This module defines the Pydantic schemas for tank status updates.
It includes models for submitting status updates and receiving status update responses,
along with validation rules for sensor readings and firmware version.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class StatusUpdateRequest(BaseModel):
    temperature: Optional[float] = Field(0.0, description="Current tank temperature in Celsius", ge=-10.0, le=50.0)
    ph: float = Field(..., description="Current tank pH level", ge=0.0, le=14.0)
    light_state: bool = Field(..., description="Whether the tank light is on")
    firmware_version: Optional[str] = Field(
        None,
        description="Tank firmware version (e.g., '1.0.0')",
        pattern=r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
    )

    @field_validator("temperature", mode="before")
    def set_default_temperature(cls, v):
        if v is None:
            return 0.0
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "temperature": 25.5,
                    "ph": 7.2,
                    "light_state": True,
                    "firmware_version": "1.0.0"
                }
            ]
        }

class StatusUpdateResponse(BaseModel):
    message: str = Field(..., description="Confirmation message")
    timestamp: datetime = Field(..., description="Time of this status update")
