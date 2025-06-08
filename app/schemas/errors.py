from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import uuid4

class ErrorResponse(BaseModel):
    """Standard error response schema for API errors."""
    detail: str = Field(..., description="A human-readable explanation of the error.")
    error_code: Optional[str] = Field(None, description="A unique error code for programmatic handling.")
    timestamp: datetime = Field(default_factory=datetime.now, description="The timestamp when the error occurred.")
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="A unique identifier for the request, useful for tracing.")

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(timespec='seconds') + '+05:30' if dt.tzinfo is None else dt.astimezone(datetime.fromtimestamp(0).astimezone().tzinfo).isoformat(timespec='seconds').replace('+00:00', '+05:30') # Ensure IST timezone for consistency in error responses
        } 