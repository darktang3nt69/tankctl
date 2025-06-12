from fastapi import APIRouter
from app.schemas.responses import StandardResponse, ErrorModel, PaginationMeta, ResponseMeta
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4
from app.utils.timezone import IST

router = APIRouter()

@router.get("/docs/response-format", tags=["documentation"], summary="Documentation for the standardized API response format")
async def get_response_format_docs():
    """
    Documentation for the standardized response format.
    
    This endpoint provides examples of the `StandardResponse` structure for successful API calls, errors, and paginated data.
    It is intended to help frontend developers understand and consume the API responses consistently.

    Returns:
        dict: Documentation and examples of the response format.
    """
    # Example data for success and error scenarios
    success_data_example = {"id": str(uuid4()), "name": "Example Item", "value": 123}
    error_details_example = {"field": "name", "reason": "invalid format"}

    # Generate example timestamps
    timestamp_example = datetime.now(IST).isoformat(timespec='milliseconds')

    return {
        "description": "Standardized API response format",
        "success_example": {
            "success": True,
            "data": success_data_example,
            "error": None,
            "meta": {
                "timestamp": timestamp_example
            }
        },
        "error_example": {
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input provided",
                "details": error_details_example
            },
            "meta": {
                "timestamp": timestamp_example
            }
        },
        "pagination_example": {
            "success": True,
            "data": [
                {"id": str(uuid4()), "name": "Item 1", "value": 1},
                {"id": str(uuid4()), "name": "Item 2", "value": 2}
            ],
            "error": None,
            "meta": {
                "timestamp": timestamp_example,
                "pagination": {
                    "total": 100,
                    "page": 1,
                    "size": 10,
                    "pages": 10
                }
            }
        }
    } 