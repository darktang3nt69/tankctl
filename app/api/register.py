from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Tank
from app.core.auth import create_access_token
from app.core.settings import settings
from pydantic import BaseModel
from datetime import datetime, UTC

router = APIRouter()

class TankRegistration(BaseModel):
    name: str
    key: str  # Pre-shared key for registration

@router.post("/register")
def register_tank(
    registration: TankRegistration,
    db: Session = Depends(get_db)
):
    # Verify pre-shared key
    if registration.key != settings.PRE_SHARED_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid registration key"
        )
    
    # Check if tank name is already taken
    existing_tank = db.query(Tank).filter(Tank.name == registration.name).first()
    if existing_tank:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tank name already registered"
        )
    
    # Create JWT token first
    token = create_access_token({"sub": registration.name})
    
    # Create new tank with token
    new_tank = Tank(
        name=registration.name,
        token=token,
        last_seen=datetime.now(UTC),
        is_active=True
    )
    db.add(new_tank)
    db.commit()
    db.refresh(new_tank)
    
    return {
        "message": "Tank registered successfully",
        "tank_id": new_tank.id,
        "token": token
    }