from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.crud import get_all_tanks, get_latest_status, get_latest_metrics, get_latest_alerts
from app.db.models import Tank
from typing import List

router = APIRouter()

@router.get("/", response_model=List[dict])
async def list_tanks(db: AsyncSession = Depends(get_db)):
    """List all tanks with their latest status and metrics."""
    tanks = await get_all_tanks()
    result = []
    for tank in tanks:
        status = await get_latest_status(tank.id)
        metrics = await get_latest_metrics(tank.id)
        alerts = await get_latest_alerts(tank.id)
        result.append({
            "id": tank.id,
            "name": tank.name,
            "status": status.dict() if status else None,
            "metrics": metrics,
            "alerts": [alert.dict() for alert in alerts]
        })
    return result

@router.get("/{tank_id}", response_model=dict)
async def get_tank(tank_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed information about a specific tank."""
    tanks = await get_all_tanks()
    tank = next((t for t in tanks if t.id == tank_id), None)
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    status = await get_latest_status(tank.id)
    metrics = await get_latest_metrics(tank.id)
    alerts = await get_latest_alerts(tank.id)
    
    return {
        "id": tank.id,
        "name": tank.name,
        "status": status.dict() if status else None,
        "metrics": metrics,
        "alerts": [alert.dict() for alert in alerts]
    } 