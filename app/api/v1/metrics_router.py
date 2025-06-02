from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.metrics_service import get_latest_status_data, get_historical_status_data, get_time_windowed_status_data
from app.schemas.status import StatusUpdateResponse # Assuming we'll return a list of these or similar
from uuid import UUID
from datetime import datetime
from typing import Optional

router = APIRouter(
    prefix="/api/v1/metrics",
    tags=["metrics"],
)

@router.get("/latest", response_model=list[StatusUpdateResponse] # Adjust response_model as needed
)
def get_latest_metrics(db: Session = Depends(get_db)):
    """
    ## Purpose
    Retrieve the most recent metrics for all tanks.

    ## Logic
    1. Query the database to get the latest status log entry for each tank.
    2. Return the latest status data.
    """
    latest_data = get_latest_status_data(db)
    # Need to convert the returned SQLAlchemy models to the response schema.
    # Assuming StatusUpdateResponse is suitable, or create a new schema.
    # For simplicity, let's return a basic structure first.
    # return latest_data # This would return SQLAlchemy objects directly, might not be desired
    
    # Converting to a list of dictionaries for a simple start.
    return [ 
        {
            "message": "Latest status", # Placeholder message, refine schema later
            "tank_id": str(item.tank_id),
            "timestamp": item.timestamp.isoformat(),
            "temperature": item.temperature,
            "ph": item.ph,
            "light_state": item.light_state,
            "firmware_version": item.firmware_version,
        } for item in latest_data
    ]

@router.get("/history/{tank_id}")
def get_historical_metrics(
    tank_id: UUID,
    start_time: Optional[datetime] = Query(None, description="Start time for the data range"),
    end_time: Optional[datetime] = Query(None, description="End time for the data range"),
    resolution: Optional[str] = Query(None, description="Time bucket interval (e.g., '1 hour', '1 day')"),
    db: Session = Depends(get_db),
):
    """
    ## Purpose
    Retrieve historical metrics for a specific tank, with optional time windowing, resolution, and gap filling.

    ## Inputs
    - **tank_id** (UUID): The unique identifier of the tank.
    - **start_time** (datetime, optional): The start of the time range.
    - **end_time** (datetime, optional): The end of the time range.
    - **resolution** (str, optional): The time bucket interval (e.g., '1 hour').
    - **db** (`Session`): SQLAlchemy database session (injected).

    ## Logic
    1. If resolution is provided, use time_bucket_gapfill to retrieve aggregated data within the time window.
    2. If no resolution, retrieve all historical data within the time window.
    3. Filter by tank_id and time range.
    4. Return the historical data.
    """
    # Call a new service function that handles time windowing and gap filling
    historical_data = get_time_windowed_status_data(db, tank_id, start_time, end_time, resolution)
    
    # Similar conversion to dictionary list as in /latest endpoint
    return [ 
        {
            "tank_id": str(item.tank_id) if hasattr(item, 'tank_id') else None, # Handle potential None for gapfill
            "timestamp": item.time.isoformat() if hasattr(item, 'time') else item.timestamp.isoformat(), # Use 'time' for aggregates
            "temperature": getattr(item, 'avg_temperature', item.temperature), # Use aggregate avg or raw
            "ph": getattr(item, 'avg_ph', item.ph), # Use aggregate avg or raw
            "light_state": item.light_state if hasattr(item, 'light_state') else None, # Light state might not aggregate meaningfully
            "firmware_version": item.firmware_version if hasattr(item, 'firmware_version') else None, # Firmware might not aggregate
        } for item in historical_data
    ] 