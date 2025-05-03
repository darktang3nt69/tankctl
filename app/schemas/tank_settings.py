# app/schemas/tank_settings.py
from pydantic import BaseModel, Field
from datetime import time
from typing import Optional

class TankSettingsResponse(BaseModel):
    light_on: Optional[time]
    light_off: Optional[time]
    is_schedule_enabled: bool
    manual_override_state: Optional[str]

    class Config:
        from_attributes = True

class TankSettingsUpdateRequest(BaseModel):
    tank_id: str = Field(..., description="UUID of the tank")
    light_on: time = Field(..., description="HH:MM lighting start")
    light_off: time = Field(..., description="HH:MM lighting end")
    is_schedule_enabled: Optional[bool] = Field(
        None, description="Enable or disable scheduled lighting"
    )