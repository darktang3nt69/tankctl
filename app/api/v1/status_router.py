# app/api/v1/status_router.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.schemas.status import StatusUpdateRequest, StatusUpdateResponse
from app.api.deps import get_db, get_current_tank
from app.services.status_service import update_tank_status
from app.schemas.error import ErrorResponse
from app.core.exceptions import TankNotFoundError

router = APIRouter()

@router.post(
    "/tank/status",
    response_model=StatusUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a heartbeat/status update from a tank",
)
def tank_status(
    request_body: StatusUpdateRequest,
    db: Session = Depends(get_db),
    tank_id: str = Depends(get_current_tank),
    req: Request = None,
) -> StatusUpdateResponse:
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
    3. Return a success response.
    4. Raise HTTP 404 if the tank is not found.

    ## Outputs
    - **Success (200):** `StatusUpdateResponse` with a confirmation message and timestamp.
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
        return update_tank_status(db, tank_id, request_body)
    except KeyError:
        raise TankNotFoundError(detail="Tank not found")
