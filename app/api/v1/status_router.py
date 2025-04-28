# app/api/v1/status_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.status import StatusUpdateRequest, StatusUpdateResponse
from app.api.deps import get_db, get_current_tank
from app.services.status_service import update_tank_status

router = APIRouter()

@router.post(
    "/tank/status",
    response_model=StatusUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a heartbeat/status update from a tank",
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
