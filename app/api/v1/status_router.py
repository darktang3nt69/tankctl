# app/api/v1/status_router.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime

from app.schemas.status import StatusUpdateRequest, StatusUpdateResponse, TankStatus
from app.api.deps import get_db, get_current_tank, get_current_user
from app.services.status_service import update_tank_status
from app.schemas.responses import StandardResponse
from app.api.utils.responses import create_success_response, create_error_response
from app.core.exceptions import TankNotFoundError
from app.services.events import publish_event, EventType
from app.crud.tank import get_tank_by_id

router = APIRouter()

@router.post(
    "/tank/status",
    response_model=StandardResponse[StatusUpdateResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit a heartbeat/status update from a tank",
)
async def tank_status(
    request_body: StatusUpdateRequest,
    db: Session = Depends(get_db),
    tank_id: str = Depends(get_current_tank),
    req: Request = None,
) -> StandardResponse[StatusUpdateResponse]:
    """
    ## Purpose
    Receive heartbeat/status updates from a tank node.

    ## Inputs
    - **request_body** (`StatusUpdateRequest`): Contains sensor readings (temperature, pH, light_state) and firmware version.
    - **db** (`Session`): SQLAlchemy database session (injected).
    - **tank_id** (`str`): The unique identifier of the tank (injected via JWT).
    - **req** (`Request`): FastAPI request object for logging (optional).

    ## Logic
    1. Extract client IP and headers for detailed logging.
    2. Call `update_tank_status` to persist the status update in the database.
    3. Publish event for status change
    4. Return a success response.
    5. Raise HTTP 404 if the tank is not found.

    ## Outputs
    - **Success (200):** `StandardResponse` with `StatusUpdateResponse` data.
    - **Error (404):** If the tank is not found.
    """
    # Detailed logging
    if req is not None:
        try:
            client_host = req.client.host
            headers = dict(req.headers)
            print(f"[TANK STATUS] From IP: {client_host}\nHeaders: {headers}\nBody: {request_body.dict()}")
        except Exception as e:
            print(f"[TANK STATUS] Logging error: {e}")
    try:
        status_response = update_tank_status(db, tank_id, request_body)
        
        # Publish event for status change
        await publish_event(
            event_type=EventType.TANK_STATUS_CHANGE,
            data={
                "tank_id": tank_id,
                "temperature": request_body.temperature,
                "ph": request_body.ph,
                "light_state": request_body.light_state,
                "firmware_version": request_body.firmware_version
            },
            tank_id=tank_id
        )

        return create_success_response(data=status_response)
    except ValueError as e:
        raise TankNotFoundError(detail=str(e))

@router.get("/tanks/{tank_id}/status", response_model=StandardResponse[TankStatus])
async def get_tank_status(
    tank_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the current status of a specific tank.
    
    This endpoint returns the latest status information for the specified tank,
    including temperature, pH, and online status.
    
    Parameters:
    - tank_id: UUID of the tank
    
    Returns:
        TankStatus: Current status of the tank
        
    Example response:
    ```json
    {
      "success": true,
      "data": {
        "tank_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Main Tank",
        "temperature": 25.5,
        "ph": 7.2,
        "online": true,
        "last_seen": "2025-06-12T10:30:00Z",
        "light_status": "on"
      },
      "meta": {
        "timestamp": "2025-06-12T10:35:00Z"
      }
    }
    ```
    
    Status codes:
    - 200: Successful operation
    - 404: Tank not found
    - 401: Unauthorized
    """
    tank = get_tank_by_id(db, tank_id)
    if not tank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tank not found")
    
    return create_success_response(
        data=TankStatus(
            tank_id=str(tank.tank_id),
            name=tank.tank_name,
            temperature=tank.temperature,
            ph=tank.ph,
            online=tank.is_online,
            last_seen=tank.last_seen,
            light_status="on" if tank.light_state else "off"
        )
    )
