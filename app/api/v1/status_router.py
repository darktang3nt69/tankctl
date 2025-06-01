# app/api/v1/status_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.status import StatusUpdateRequest, StatusUpdateResponse
from app.api.deps import get_db, get_current_tank
from app.services.status_service import update_tank_status
from app.schemas.error import ErrorResponse

router = APIRouter()

@router.post(
    "/tank/status",
    response_model=StatusUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a heartbeat/status update from a tank",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "default": {
                            "summary": "Tank status update",
                            "value": {
                                "temperature": 25.5,
                                "ph": 7.2,
                                "light_state": True,
                                "firmware_version": "1.0.0"
                            }
                        }
                    }
                }
            }
        },
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "examples": {
                            "success": {
                                "summary": "Status update success",
                                "value": {
                                    "message": "Status updated successfully",
                                    "timestamp": "2024-06-01T12:00:00+05:30"
                                }
                            }
                        }
                    }
                }
            },
            "404": {
                "description": "Tank not found.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "examples": {
                            "not_found": {
                                "summary": "Tank not found",
                                "value": {"detail": "Tank not found"}
                            }
                        }
                    }
                }
            },
            "500": {
                "description": "Internal server error.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "examples": {
                            "server_error": {
                                "summary": "Internal error",
                                "value": {"detail": "Internal server error"}
                            }
                        }
                    }
                }
            }
        }
    }
)
def tank_status(
    request: StatusUpdateRequest,
    db: Session = Depends(get_db),
    tank_id: str = Depends(get_current_tank),
) -> StatusUpdateResponse:
    """
    Receive heartbeat/status updates from a tank node.

    - Requires Bearer token authentication.
    - Updates tank's last_seen and logs the provided status (temperature, pH, light).
    """
    try:
        return update_tank_status(db, tank_id, request)
    except KeyError:
        raise HTTPException(status_code=404, detail="Tank not found")
