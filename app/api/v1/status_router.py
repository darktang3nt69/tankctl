from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.status import StatusUpdateRequest, StatusUpdateResponse
from app.services.status_service import update_tank_status
from app.api.deps import get_db, get_current_tank

router = APIRouter()

@router.post(
    "/tank/status",
    response_model=StatusUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a status update for a tank",
)
def tank_status(
    request: StatusUpdateRequest,
    tank_id: str = Depends(get_current_tank),
    db: Session = Depends(get_db),
) -> StatusUpdateResponse:
    """
    - Requires a valid Bearer JWT (extracts tank_id via get_current_tank)
    - Updates last_seen and writes a StatusLog entry
    """
    try:
        return update_tank_status(db, tank_id, request)
    except KeyError:
        raise HTTPException(status_code=404, detail="Tank not found")
