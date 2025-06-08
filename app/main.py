from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.v1.register_router import router as register_router
from app.api.v1.status_router import router as status_router
from app.api.v1.command_router import router as command_router
from app.api.v1.admin_command_router import router as admin_command_router
# from app.api.v1.override_router import router as override_router
from app.api.v1.settings_router import router as settings_router
from app.api.v1.metrics_router import router as metrics_router
from app.core.config import settings

from prometheus_fastapi_instrumentator import Instrumentator

from prometheus_client import Gauge
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.tank import Tank
from app.models.tank_settings import TankSettings
from app.metrics.tank_metrics import tank_online_status
import asyncio

# Import database components
from app.core.database import Base, engine

# 🚨 NEW: Explicitly import models
from app.models import tank, event_log

from fastapi.middleware.cors import CORSMiddleware

from app.schemas.error import ErrorResponse
from app.core.exceptions import TankNotFoundError, InvalidCommandError, DatabaseError

from app.core.logging_config import configure_logging
from app.core.logging_middleware import LoggingMiddleware

from app.utils.timezone import IST # Import IST
from datetime import datetime
from json import JSONEncoder


app = FastAPI(
    title="AquaPi Tank API",
    description="API to manage and monitor aquarium tanks",
    version="1.0.0"
)

# Custom JSON encoder for datetime objects to ensure IST with offset
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # Ensure the datetime object is timezone-aware
            if obj.tzinfo is None:
                # If naive, assume it's in IST and make it aware
                return obj.replace(tzinfo=IST).isoformat(timespec='microseconds')
            else:
                # If already timezone-aware, convert to IST and format
                return obj.astimezone(IST).isoformat(timespec='microseconds')
        return JSONEncoder.default(self, obj)

# Assign the custom encoder to FastAPI app
app.json_encoder = CustomJSONEncoder

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or limit to Grafana origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

instrumentator = Instrumentator().instrument(app)

# ✅ Auto-create tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    instrumentator.expose(app, include_in_schema=False, should_gzip=True, endpoint="/metrics")

configure_logging()

# Include your API routers
# Mount versioned routes
app.include_router(register_router, prefix="/api/v1")
app.include_router(status_router,   prefix="/api/v1")
app.include_router(command_router, prefix="/api/v1")
app.include_router(admin_command_router, prefix="/api/v1")
# app.include_router(override_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {"message": "TankCTL API is up and running"}


from app.metrics.updater import update_tank_metrics

@app.on_event("startup")
async def start_metrics_updater():
    asyncio.create_task(update_tank_metrics())

@app.get("/openapi-error-model", response_model=ErrorResponse, include_in_schema=False)
def _openapi_error_model():
    return {"detail": "This is a dummy endpoint to include ErrorResponse in OpenAPI."}

@app.exception_handler(TankNotFoundError)
def tank_not_found_exception_handler(request: Request, exc: TankNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=exc.detail).dict(),
    )

@app.exception_handler(InvalidCommandError)
def invalid_command_exception_handler(request: Request, exc: InvalidCommandError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=exc.detail).dict(),
    )

@app.exception_handler(DatabaseError)
def database_error_exception_handler(request: Request, exc: DatabaseError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=exc.detail).dict(),
    )

@app.get("/api/v1/tanks", tags=["Admin", "Debug"])
def list_tanks():
    """
    List all registered tanks and their basic info.
    """
    db = SessionLocal()
    try:
        tanks = db.query(Tank).all()
        return {
            "count": len(tanks),
            "tanks": [
                {
                    "tank_id": str(t.tank_id),
                    "tank_name": t.tank_name,
                    "location": t.location,
                    "is_online": t.is_online,
                    "last_seen": t.last_seen.isoformat() if t.last_seen else None,
                }
                for t in tanks
            ]
        }
    finally:
        db.close()