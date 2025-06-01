# app/schemas/tank.py

from pydantic import BaseModel, Field, field_validator, field_serializer
from datetime import datetime, time
from typing import Optional
from zoneinfo import ZoneInfo
import re

IST = ZoneInfo("Asia/Kolkata")

# RegEx: allow "9:05" or "09:05" from 00:00–23:59
_HH = r"(?:[01]?\d|2[0-3])"
_MM = r"[0-5]\d"
TIME_RE = re.compile(rf"^{_HH}:{_MM}$")

class TankRegisterRequest(BaseModel):
    auth_key: str = Field(..., description="Authentication key required for tank registration")
    tank_name: str = Field(..., description="Unique name identifier for the tank")
    location: Optional[str] = Field(None, description="Physical location or description of where the tank is installed")
    firmware_version: Optional[str] = Field(None, description="Current version of the tank's firmware")

    light_on: Optional[str] = Field(None, description="Time when tank lights turn on in 24-hour format (HH:MM)")
    light_off: Optional[str] = Field(None, description="Time when tank lights turn off in 24-hour format (HH:MM)")

    @field_validator("light_on", "light_off", mode="before")
    def default_and_pad(cls, v, info):
        # default to 10:00 or 16:00 if missing
        if v is None:
            return "10:00" if info.field_name == "light_on" else "16:00"
        v = v.strip()
        # pad single‐digit hour
        h, m = v.split(":")
        if len(h) == 1:
            v = f"0{h}:{m}"
        if not TIME_RE.match(v):
            raise ValueError("must be HH:MM between 00:00 and 23:59")
        return v

    @field_validator("light_on", "light_off")
    def to_ist_time(cls, v: str) -> time:
        # parse and attach IST tzinfo
        t0 = datetime.strptime(v, "%H:%M").time()
        return t0.replace(tzinfo=IST)

    class Config:
        from_attributes = True


class TankRegisterResponse(BaseModel):
    message: str = Field(..., description="Status message indicating the result of the registration")
    tank_id: str = Field(..., description="Unique identifier assigned to the registered tank")
    access_token: str = Field(..., description="Authentication token for future API requests")
    firmware_version: Optional[str] = Field(None, description="Current version of the tank's firmware")
    light_on: time = Field(..., description="Configured time when tank lights turn on")
    light_off: time = Field(..., description="Configured time when tank lights turn off")
    is_schedule_enabled: bool = Field(..., description="Indicates whether the light schedule is enabled")

    model_config = {"from_attributes": True}

    @field_serializer("light_on", "light_off", mode="plain")
    def _fmt_time(self, v: time) -> str:
        # Drop seconds & offset, render "HH:MM"
        return v.strftime("%H:%M")
