from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class StatusUpdateRequest(BaseModel):
    temperature: Optional[float] = Field(0.0, description="Current tank temperature")
    ph: float = Field(..., description="Current tank pH level")
    light_state: bool = Field(..., description="Whether the tank light is on")
    firmware_version: Optional[str] = Field(None, description="Tank firmware version")

    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()
        yield cls._default_temperature

    @staticmethod
    def _default_temperature(values):
        # If temperature is None, set it to 0.0
        if values.get('temperature', 0.0) is None:
            values['temperature'] = 0.0
        return values

class StatusUpdateResponse(BaseModel):
    message: str = Field(..., description="Confirmation message")
    timestamp: datetime = Field(..., description="Time of this status update")
