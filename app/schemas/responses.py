from typing import Generic, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.utils.timezone import IST # Import IST for timezone handling

T = TypeVar('T')

class ErrorModel(BaseModel):
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class PaginationMeta(BaseModel):
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")

class ResponseMeta(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(IST), description="Response timestamp in ISO format")
    pagination: Optional[PaginationMeta] = Field(None, description="Pagination information if applicable")

    class Config:
        json_encoders = {
            datetime: lambda v: v.astimezone(IST).isoformat(timespec='milliseconds')
        }

class StandardResponse(BaseModel, Generic[T]):
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    error: Optional[ErrorModel] = Field(None, description="Error information if success is false")
    meta: ResponseMeta = Field(default_factory=lambda: ResponseMeta(), description="Metadata about the response") 