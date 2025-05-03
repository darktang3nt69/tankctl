# app/schemas/tank_settings.py

from pydantic import BaseModel, Field, field_validator, field_serializer
from datetime import datetime, time
from typing import Optional
from zoneinfo import ZoneInfo
import re
from uuid import UUID


IST = ZoneInfo("Asia/Kolkata")

_HH = r"(?:[01]?\d|2[0-3])"
_MM = r"[0-5]\d"
TIME_RE = re.compile(rf"^{_HH}:{_MM}$")

class TankSettingsResponse(BaseModel):
    tank_id: UUID
    light_on: time
    light_off: time
    is_schedule_enabled: bool
    manual_override_state: Optional[str]
    last_schedule_check_on: Optional[datetime]
    last_schedule_check_off: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_serializer("light_on", "light_off", mode="plain")
    def _fmt_time(self, v: time) -> str:
        return v.strftime("%H:%M")


class TankSettingsUpdateRequest(BaseModel):
    tank_id: UUID
    light_on:  str = Field(..., description="HH:MM (24h)")
    light_off: str = Field(..., description="HH:MM (24h)")
    is_schedule_enabled: bool

    @field_validator("light_on", "light_off", mode="before")
    def pad_and_validate(cls, v):
        v = v.strip()
        h, m = v.split(":")
        if len(h) == 1:
            v = f"0{h}:{m}"
        if not TIME_RE.match(v):
            raise ValueError("must be HH:MM between 00:00 and 23:59")
        return v

    @field_validator("light_on", "light_off")
    def to_ist_time(cls, v: str) -> time:
        t0 = datetime.strptime(v, "%H:%M").time()
        return t0.replace(tzinfo=IST)

    class Config:
        from_attributes = True
    