from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.tank import TankRegisterRequest, TankRegisterResponse
from app.services.tank_service import register_tank
from app.api.deps import get_db

router = APIRouter()

@router.post(
    "/tank/register",
    response_model=TankRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new tank node",
)
def tank_register(
    request: TankRegisterRequest,
    db: Session = Depends(get_db),
) -> TankRegisterResponse:
    """
    Register a tank if not already registered.
    If already registered (based on tank name), return the same JWT token.
    """
    try:
        return register_tank(db, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
