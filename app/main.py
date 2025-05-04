from fastapi import FastAPI
from app.api.v1.register_router import router as register_router
from app.api.v1.status_router import router as status_router
from app.api.v1.command_router import router as command_router
from app.api.v1.admin_command_router import router as admin_command_router
# from app.api.v1.override_router import router as override_router
from app.api.v1.settings_router import router as settings_router
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


# import logging.config
# from app.utils.logging_config import LOGGING_CONFIG

# logging.config.dictConfig(LOGGING_CONFIG)

# Import database components
from app.core.database import Base, engine

# 🚨 NEW: Explicitly import models
from app.models import tank, event_log

from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(
    title="AquaPi Tank API",
    description="API to manage and monitor aquarium tanks",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or limit to Grafana origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator = Instrumentator().instrument(app)

# ✅ Auto-create tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    instrumentator.expose(app, include_in_schema=False, should_gzip=True, endpoint="/metrics")

# Include your API routers
# Mount versioned routes
app.include_router(register_router, prefix="/api/v1")
app.include_router(status_router,   prefix="/api/v1")
app.include_router(command_router, prefix="/api/v1")
app.include_router(admin_command_router, prefix="/api/v1")
# app.include_router(override_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {"message": "AquaPi API is up and running"}


from app.metrics.updater import update_tank_metrics

@app.on_event("startup")
async def start_metrics_updater():
    asyncio.create_task(update_tank_metrics())