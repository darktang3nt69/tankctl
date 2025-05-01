from pydantic import BaseModel
from datetime import time
from typing import Optional

class TankRegisterRequest(BaseModel):
    auth_key: str
    tank_name: str
    location: Optional[str] = None
    firmware_version: Optional[str] = None

class TankRegisterResponse(BaseModel):
    tank_id: str
    access_token: str

class TankSettingsResponse(BaseModel):
    tank_id: str
    light_on: time
    light_off: time
    manual_override_state: Optional[str] = None