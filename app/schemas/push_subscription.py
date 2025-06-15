from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class NotificationPreferences(BaseModel):
    disable_offline: bool = Field(False, description="Disable tank offline notifications")
    disable_temperature_alert: bool = Field(False, description="Disable temperature alert notifications")
    disable_ph_alert: bool = Field(False, description="Disable pH alert notifications")
    disable_command_completed: bool = Field(False, description="Disable command completed notifications")
    disable_command_failed: bool = Field(False, description="Disable command failed notifications")
    quiet_hours_start: Optional[int] = Field(None, description="Start hour for quiet hours (0-23)")
    quiet_hours_end: Optional[int] = Field(None, description="End hour for quiet hours (0-23)")

class PushSubscriptionBase(BaseModel):
    endpoint: str = Field(..., description="Push subscription endpoint URL")
    p256dh: str = Field(..., description="P-256 Diffie-Hellman public key")
    auth: str = Field(..., description="Authentication secret")
    user_agent: Optional[str] = Field(None, description="User agent string")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Notification preferences")

class PushSubscriptionCreate(PushSubscriptionBase):
    pass

class PushSubscriptionUpdate(BaseModel):
    preferences: NotificationPreferences = Field(..., description="Updated notification preferences")

class PushSubscription(PushSubscriptionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True 