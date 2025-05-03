# app/schemas/tank.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import time, datetime

class TankRegisterRequest(BaseModel):
    auth_key: str
    tank_name: str

    # Truly optional
    location: Optional[str] = None
    firmware_version: Optional[str] = None

    # HH:MM strings; validated via pattern
    light_on: Optional[str] = Field(
        None,
        pattern=r"^[0-2]\d:[0-5]\d$",
        description="Lighting start time in HH:MM format",
    )
    light_off: Optional[str] = Field(
        None,
        pattern=r"^[0-2]\d:[0-5]\d$",
        description="Lighting end time in HH:MM format",
    )

    @field_validator("light_on", "light_off", mode="before")
    def set_default(cls, v, info):
        if v is None:
            return "10:00" if info.field_name == "light_on" else "16:00"
        return v

    @field_validator("light_on", "light_off")
    def parse_time(cls, v):
        return datetime.strptime(v, "%H:%M").time()


class TankRegisterResponse(BaseModel):
    message: str
    tank_id: str
    access_token: str
    firmware_version: Optional[str]
    light_on: time
    light_off: time
    is_schedule_enabled: bool

    model_config = {"from_attributes": True}
