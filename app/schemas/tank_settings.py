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
        orm_mode = True

class TankSettingsUpdateRequest(BaseModel):
    light_on: time = Field(..., description="Time to turn lights on (HH:MM:SS)")
    light_off: time = Field(..., description="Time to turn lights off (HH:MM:SS)")
    is_schedule_enabled: Optional[bool] = Field(
        None, description="Enable or disable scheduled lighting"
    )
