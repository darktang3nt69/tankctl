from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class StatusUpdateRequest(BaseModel):
    temperature: float = Field(..., description="Current tank temperature")
    ph: float = Field(..., description="Current tank pH level")
    light_state: bool = Field(..., description="Whether the tank light is on")
    firmware_version: Optional[str] = Field(None, description="Tank firmware version")

class StatusUpdateResponse(BaseModel):
    message: str = Field(..., description="Confirmation message")
    timestamp: datetime = Field(..., description="Time of this status update")
