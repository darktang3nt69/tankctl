# app/schemas/admin_command.py

from pydantic import BaseModel
from uuid import UUID

class AdminSendCommandRequest(BaseModel):
    tank_id: UUID
    command_payload: str
