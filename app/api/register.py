from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import Tank
from app.core.auth import create_access_token
from app.core.settings import settings
from pydantic import BaseModel
from datetime import datetime, UTC
from app.tasks.notifications import send_discord_notification

router = APIRouter()

class TankRegistration(BaseModel):
    name: str
    key: str  # Pre-shared key for registration
    test_mode: bool = False  # Optional flag for test mode

@router.post("/register")
async def register_tank(
    registration: TankRegistration,
    db: AsyncSession = Depends(get_db)
):
    # Verify pre-shared key
    if registration.key != settings.PRE_SHARED_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid registration key"
        )
    
    # Check if tank name is already taken
    result = await db.execute(
        select(Tank).where(Tank.name == registration.name)
    )
    existing_tank = result.scalar_one_or_none()
    
    if existing_tank:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tank name already registered"
        )
    
    # Create JWT token first
    token = create_access_token({"sub": registration.name, "test_mode": registration.test_mode})
    
    # Create new tank with token and test mode flag
    new_tank = Tank(
        name=registration.name,
        token=token,
        last_seen=datetime.now(UTC),
        is_active=True,
        test_mode=registration.test_mode
    )
    db.add(new_tank)
    await db.commit()
    await db.refresh(new_tank)
    
    # Send registration notification
    if not registration.test_mode:  # Only send notifications for non-test tanks
        send_discord_notification.delay(
            f"🆕 New tank registered: **{new_tank.name}** (ID: {new_tank.id})",
            tank_id=new_tank.id
        )
    
    return {
        "message": "Tank registered successfully",
        "tank_id": new_tank.id,
        "name": new_tank.name,
        "token": token,
        "test_mode": registration.test_mode
    }