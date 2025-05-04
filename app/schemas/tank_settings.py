from pydantic import BaseModel, Field, field_validator, field_serializer
from datetime import datetime, time
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo
import re

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

    # New pause‑until marker
    schedule_paused_until: Optional[datetime]

    # Last scheduled on/off timestamps
    last_schedule_check_on:  Optional[datetime]
    last_schedule_check_off: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_serializer("light_on", "light_off", mode="plain")
    def _fmt_time(self, v: time) -> str:
        # emit HH:MM
        return v.strftime("%H:%M")

    @field_serializer(
        "schedule_paused_until",
        "last_schedule_check_on",
        "last_schedule_check_off",
        mode="plain"
    )
    def _fmt_datetime(self, v: Optional[datetime]) -> Optional[str]:
        # emit ISO‑style local IST timestamp, or null
        if v is None:
            return None
        return v.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")


class TankSettingsUpdateRequest(BaseModel):
    # (you can drop tank_id here if your route takes it as a path param)
    tank_id: UUID
    light_on:  Optional[str] = Field(None, description="HH:MM (24h), IST")
    light_off: Optional[str] = Field(None, description="HH:MM (24h), IST")
    is_schedule_enabled: Optional[bool] = Field(
        None,
        description="Enable or disable automated scheduling"
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
        return t0.replace(tzinfo=IST)

    model_config = {"from_attributes": True}


class TankOverrideRequest(BaseModel):
    tank_id: UUID
    override_command: str = Field(
        ...,
        pattern="^(light_on|light_off)$",
        description="Either 'on' (force light on) or 'off' (force light off)"
    )

    model_config = {"from_attributes": True}
