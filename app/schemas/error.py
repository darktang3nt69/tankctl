from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="A human-readable error message.") 