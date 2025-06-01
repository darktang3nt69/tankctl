# app/schemas/admin_command.py

from pydantic import BaseModel, Field
from uuid import UUID

class AdminSendCommandRequest(BaseModel):
    tank_id: UUID = Field(..., description="Unique identifier of the tank to send the admin command to")
    command_payload: str = Field(..., description="Admin command to be executed (e.g., 'restart', 'update_firmware', 'reset_settings')")
