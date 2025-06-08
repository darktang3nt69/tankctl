"""
Tank Settings Schemas

This module defines the Pydantic schemas for managing tank lighting settings,
including request and response models for fetching, updating, and overriding settings.
It incorporates validation rules for time formats and schedule consistency.
"""
from pydantic import BaseModel, Field, field_validator, field_serializer, model_validator
from datetime import datetime, time
from typing import Optional, Self
from uuid import UUID
from zoneinfo import ZoneInfo
import re

IST = ZoneInfo("Asia/Kolkata")

# allow "9:05" or "09:05" from 00–23 / 00–59
_HH = r"(?:[01]?\d|2[0-3])"
_MM = r"[0-5]\d"
TIME_RE = re.compile(rf"^{_HH}:{_MM}$")


class TankSettingsResponse(BaseModel):
    tank_id: UUID = Field(..., description="Unique identifier of the tank")
    light_on: time = Field(..., description="Configured time when tank lights turn on")
    light_off: time = Field(..., description="Configured time when tank lights turn off")
    is_schedule_enabled: bool = Field(..., description="Indicates whether the light schedule is enabled")

    # New pause‑until marker
    schedule_paused_until: Optional[datetime] = Field(None, description="Timestamp until which the schedule is paused")

    # Last scheduled on/off timestamps
    last_schedule_check_on: Optional[datetime] = Field(None, description="Last timestamp when the light was turned on according to schedule")
    last_schedule_check_off: Optional[datetime] = Field(None, description="Last timestamp when the light was turned off according to schedule")

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
    tank_id: UUID = Field(..., description="Unique identifier of the tank to update settings for")
    light_on: Optional[str] = Field(None, description="New time for lights to turn on in 24-hour format (HH:MM), IST timezone")
    light_off: Optional[str] = Field(None, description="New time for lights to turn off in 24-hour format (HH:MM), IST timezone")
    is_schedule_enabled: Optional[bool] = Field(
        None,
        description="Set to true to enable automated light scheduling, false to disable"
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
            raise ValueError("Time must be in HH:MM format between 00:00 and 23:59.")
        return v

    @field_validator("light_on", "light_off")
    def to_ist_time(cls, v: Optional[str]) -> Optional[time]:
        if v is None:
            return None
        t0 = datetime.strptime(v, "%H:%M").time()
        return t0.replace(tzinfo=IST)

    @model_validator(mode='after')
    def validate_schedule_consistency(self) -> Self:
        if self.is_schedule_enabled is True:
            if self.light_on is None or self.light_off is None:
                raise ValueError("light_on and light_off must be provided when is_schedule_enabled is True.")
        elif self.is_schedule_enabled is False:
            if self.light_on is not None or self.light_off is not None:
                raise ValueError("light_on and light_off must be None when is_schedule_enabled is False.")
        return self

    model_config = {"from_attributes": True}


class TankOverrideRequest(BaseModel):
    tank_id: UUID = Field(..., description="Unique identifier of the tank to override")
    override_command: str = Field(
        ...,
        pattern="^(light_on|light_off)$",
        description="Command to override light state: 'light_on' to force lights on, 'light_off' to force lights off"
    )

    model_config = {"from_attributes": True}
