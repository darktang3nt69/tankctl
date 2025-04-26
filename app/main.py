from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import register, status, commands, config, tanks, schedules, events
from app.core.config import settings
from app.core.auth import get_current_tank
from app.core.rate_limit import RateLimitMiddleware
from app.db.init_db import init_db
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
from app.core.metrics import get_metrics
import psutil
import time
import asyncio
from prometheus_client import Counter, Gauge, Histogram

# Define metrics
cpu_usage = Gauge('tankctl_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('tankctl_memory_usage_bytes', 'Memory usage in bytes')
tank_temperature = Gauge('tankctl_temperature_celsius', 'Tank temperature in Celsius')
tank_ph_level = Gauge('tankctl_ph_level', 'Tank pH level')
tank_water_level = Gauge('tankctl_water_level_percent', 'Tank water level percentage')
command_queue_size = Gauge('tankctl_command_queue_size', 'Number of pending commands')
node_health = Gauge('tankctl_node_health', 'Node health status (1=healthy, 0=unhealthy)')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Print settings for debugging
logger.info(f"Settings loaded: PRE_SHARED_KEY={settings.PRE_SHARED_KEY}")

# Initialize the database
init_db()

app = FastAPI(
    title="TankCTL - Aquarium Control API",
    description="A Kubernetes-Inspired Control Plane for Smart Aquariums",
    version="1.0.0"
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# CORS for Grafana
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consider tightening in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid request data",
            "errors": exc.errors()
        },
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid data format",
            "errors": exc.errors()
        },
    )

# Routes
app.include_router(register.router)
app.include_router(status.router, dependencies=[Depends(get_current_tank)])
app.include_router(commands.router, dependencies=[Depends(get_current_tank)])
app.include_router(config.router, dependencies=[Depends(get_current_tank)])
app.include_router(tanks.router, prefix="/api/tanks", tags=["tanks"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
app.include_router(events.router, prefix="/api/events", tags=["events"])

@app.get("/")
def root():
    return {
        "message": "Aquarium Control API is live",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return get_metrics()

@app.on_event("startup")
async def startup_event():
    # Start background task for metrics collection
    asyncio.create_task(collect_metrics())

async def collect_metrics():
    """Background task to collect and update metrics."""
    while True:
        try:
            # Update system resource metrics
            process = psutil.Process()
            cpu_usage.labels(instance="tankctl").set(process.cpu_percent())
            memory_usage.labels(instance="tankctl").set(process.memory_info().rss)
            
            # Update tank metrics
            for tank in await get_all_tanks():
                tank_temperature.labels(tank_id=str(tank.id)).set(tank.temperature)
                tank_ph_level.labels(tank_id=str(tank.id)).set(tank.ph_level)
                tank_water_level.labels(tank_id=str(tank.id)).set(tank.water_level)
                
                # Update command queue size
                queue_size = await get_command_queue_size(tank.id)
                command_queue_size.labels(tank_id=str(tank.id)).set(queue_size)
                
                # Update node health
                health_status = 1 if tank.is_healthy else 0
                node_health.labels(tank_id=str(tank.id)).set(health_status)
            
            await asyncio.sleep(15)  # Update every 15 seconds
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            await asyncio.sleep(60)  # Wait longer on error