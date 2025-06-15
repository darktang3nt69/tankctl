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

@router.get("/docs/frontend-integration", tags=["documentation"])
async def frontend_integration_guide():
    """
    Frontend integration guide for the TankCtl API.
    
    This endpoint provides comprehensive documentation on how to integrate
    the frontend with the TankCtl API, including code examples and best practices.
    
    Topics covered:
    - Authentication and token handling
    - Real-time updates with SSE
    - Fetching tank status and metrics
    - Issuing commands to tanks
    - Handling historical data for charts
    - Push notifications
    - Error handling
    """
    return {
        "authentication": {
            "endpoint": "/api/v1/auth/token",
            "method": "POST",
            "example": "See /api/v1/auth/docs for detailed authentication examples"
        },
        "real_time_updates": {
            "endpoint": "/api/v1/events",
            "method": "GET",
            "example": "See /api/v1/events/docs for detailed SSE examples"
        },
        "tank_status": {
            "endpoint": "/api/v1/tanks/{tank_id}/status",
            "method": "GET",
            "example": "async function getTankStatus(tankId) {\n  return await fetchData(`/api/v1/tanks/${tankId}/status`);\n}"
        },
        "command_issuance": {
            "endpoint": "/api/v1/commands",
            "method": "POST",
            "example": "async function issueCommand(tankId, commandType, parameters = {}) {\n  return await fetchWithAuth('/api/v1/commands', {\n    method: 'POST',\n    body: JSON.stringify({ tank_id: tankId, command_type: commandType, parameters })\n  });\n}"
        },
        "historical_data": {
            "endpoint": "/api/v1/metrics/history/{tank_id}",
            "method": "GET",
            "example": "async function getHistoricalData(tankId, startTime, endTime, resolution) {\n  const params = new URLSearchParams();\n  if (startTime) params.append('start_time', startTime);\n  if (endTime) params.append('end_time', endTime);\n  if (resolution) params.append('resolution', resolution);\n  return await fetchData(`/api/v1/metrics/history/${tankId}?${params}`);\n}"
        },
        "push_notifications": {
            "setup_endpoint": "/api/v1/push/vapid-public-key",
            "subscribe_endpoint": "/api/v1/push/subscribe",
            "example": "See /api/v1/push/subscribe documentation for detailed push notification examples"
        },
        "error_handling": {
            "example": "async function fetchWithErrorHandling(url) {\n  try {\n    const response = await fetchData(url);\n    if (!response.success) {\n      throw new Error(response.error.message);\n    }\n    return response.data;\n  } catch (error) {\n    console.error('API Error:', error);\n    // Handle error appropriately\n    throw error;\n  }\n}"
        },
        "common_patterns": {
            "polling": "For non-critical updates, poll endpoints every 5-30 seconds",
            "caching": "Cache responses to reduce API calls",
            "optimistic_updates": "Update UI immediately, then confirm with API response"
        }
    } 