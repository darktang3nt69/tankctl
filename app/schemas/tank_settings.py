# app/schemas/tank_settings.py

from pydantic import BaseModel, Field, field_validator, field_serializer
from datetime import datetime, time
from typing import Optional, Literal
from zoneinfo import ZoneInfo
import re
from uuid import UUID

IST = ZoneInfo("Asia/Kolkata")

# allow “9:05” or “09:05” from 00–23 / 00–59
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
        # always return HH:MM (IST) to the client
        return v.strftime("%H:%M")


class TankSettingsUpdateRequest(BaseModel):
    tank_id: UUID

    # all optional now
    light_on:  Optional[str] = Field(
        None, description="HH:MM (24h), IST"
    )
    light_off: Optional[str] = Field(
        None, description="HH:MM (24h), IST"
    )
    is_schedule_enabled: Optional[bool] = Field(
        None, description="Enable or disable scheduling"
    )

    @field_validator("light_on", "light_off", mode="before")
    def pad_and_validate(cls, v):
        if v is None:
            return None
        v = v.strip()
        h, m = v.split(":")
        if len(h) == 1:
            v = f"0{h}:{m}"
        if not TIME_RE.match(v):
            raise ValueError("must be HH:MM between 00:00 and 23:59")
        return v

    @field_validator("light_on", "light_off")
    def to_ist_time(cls, v: Optional[str]) -> Optional[time]:
        if v is None:
            return None
        t0 = datetime.strptime(v, "%H:%M").time()
        # attach IST tzinfo so your scheduler sees it correctly
        return t0.replace(tzinfo=IST)

    class Config:
        from_attributes = True


class TankOverrideRequest(BaseModel):
    tank_id: UUID
    override_state: Literal["on", "off"] = Field(
        ...,
        description="Either 'on' or 'off'"
    )

    class Config:
        from_attributes = True
