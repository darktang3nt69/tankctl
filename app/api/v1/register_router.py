"""
# Register Router

This module provides API endpoints for registering new tank nodes with the system.

## Endpoints
- **POST /tank/register**: Register a new tank node and receive a JWT token.

Purpose: Allow new tank nodes to securely join the system and receive authentication credentials.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.tank import TankRegisterRequest, TankRegisterResponse
from app.services.tank_service import register_tank
from app.api.deps import get_db
from app.core.exceptions import AuthenticationError

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
    ## Purpose
    Register a new tank node and issue a JWT token for authentication.

    ## Inputs
    - **request** (`TankRegisterRequest`): Contains tank name and registration details.
    - **db** (`Session`): SQLAlchemy database session (injected).

    ## Logic
    1. Attempt to register the tank using `register_tank` service.
    2. If the tank is already registered (by name), return the existing JWT token.
    3. If registration fails, raise HTTP 401.

    ## Outputs
    - **Success (201):** `TankRegisterResponse` with JWT token and tank details.
    - **Error (401):** `detail` (str): Error message if registration fails.
    """
    try:
        return register_tank(db, request)
    except ValueError as e:
        raise AuthenticationError(detail=str(e))
