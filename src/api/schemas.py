"""
Pydantic schemas for TankCtl API.
"""

from pydantic import BaseModel
from typing import Optional, Dict


class DeviceRegisterRequest(BaseModel):
    """Request to register a new device."""

    device_id: str
    device_secret: str


class DeviceResponse(BaseModel):
    """Device response model."""

    device_id: str
    status: str
    firmware_version: Optional[str] = None
    created_at: Optional[str] = None
    last_seen: Optional[str] = None


class CommandRequest(BaseModel):
    """Request to send a command to device."""

    command: str
    value: Optional[str] = None
    version: Optional[int] = None


class CommandSendRequest(BaseModel):
    """Request to send a command to device."""

    command: str
    value: Optional[str] = None
    version: Optional[int] = None


class CommandResponse(BaseModel):
    """Command response model."""

    command_id: Optional[str] = None
    device_id: str
    command: str
    value: Optional[str] = None
    version: int
    status: str
    created_at: Optional[str] = None


class DeviceShadowUpdateRequest(BaseModel):
    """Request to update device shadow desired state."""

    desired: Dict


class DeviceShadowResponse(BaseModel):
    """Device shadow response model."""

    device_id: str
    desired: Dict
    reported: Dict
    version: int
    synchronized: bool


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    message: str
