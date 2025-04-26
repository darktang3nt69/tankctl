from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from app.api import register, status, commands, config, tanks, schedules, events, health
from app.core.config import settings
from app.core.auth import get_current_tank
from app.core.rate_limit import RateLimitMiddleware
from app.db.init_db import init_db_async
from app.db.crud import get_all_tanks, get_command_queue_size
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
from app.core.metrics import get_metrics
import psutil
import time
import asyncio
import httpx
from prometheus_client import Counter, Gauge, Histogram
from app.tasks.notifications import send_discord_notification
from app.api.health import check_service

# Define metrics
cpu_usage = Gauge('tankctl_cpu_usage_percent', 'CPU usage percentage', ['instance'])
memory_usage = Gauge('tankctl_memory_usage_bytes', 'Memory usage in bytes', ['instance'])
tank_temperature = Gauge('tankctl_temperature_celsius', 'Tank temperature in Celsius', ['tank_id'])
tank_ph_level = Gauge('tankctl_ph_level', 'Tank pH level', ['tank_id'])
tank_water_level = Gauge('tankctl_water_level_percent', 'Tank water level percentage', ['tank_id'])
command_queue_size = Gauge('tankctl_command_queue_size', 'Number of pending commands', ['tank_id'])
node_health = Gauge('tankctl_node_health', 'Node health status (1=healthy, 0=unhealthy)', ['tank_id'])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Print settings for debugging
logger.info(f"Settings loaded: PRE_SHARED_KEY={settings.PRE_SHARED_KEY}")

app = FastAPI(
    title="TankCTL - Aquarium Control API",
    description="A Kubernetes-Inspired Control Plane for Smart Aquariums",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup."""
    # Wait for database to be ready
    max_retries = 5
    retry_delay = 5
    for i in range(max_retries):
        try:
            await init_db_async()
            logger.info("Database initialized successfully")
            break
        except Exception as e:
            if i == max_retries - 1:
                logger.error(f"Failed to initialize database after {max_retries} attempts: {str(e)}")
                raise
            logger.warning(f"Database initialization attempt {i+1} failed: {str(e)}")
            await asyncio.sleep(retry_delay)
    
    # Start background task for metrics collection
    asyncio.create_task(collect_metrics())
    
    # Send startup notification
    try:
        # Get system metrics for the notification
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        message = "🚀 **TankCTL API Started**\n\n"
        
        # Check service health
        message += "🔍 **Service Health**\n"
        
        # Check Redis
        try:
            from app.core.redis import redis_client
            redis_client.ping()
            message += "✅ Redis: Healthy\n"
        except Exception as e:
            message += f"❌ Redis: Unhealthy ({str(e)})\n"
        
        # Check Database
        try:
            from sqlalchemy import text
            from app.db.session import get_sync_db
            db = next(get_sync_db())
            db.execute(text("SELECT 1"))
            message += "✅ Database: Healthy\n"
            db.close()
        except Exception as e:
            message += f"❌ Database: Unhealthy ({str(e)})\n"
        
        # Check Celery
        try:
            celery_workers = redis_client.llen("celery")
            if celery_workers > 0:
                message += "✅ Celery: Healthy\n"
            else:
                message += "❌ Celery: No workers found\n"
        except Exception as e:
            message += f"❌ Celery: Unhealthy ({str(e)})\n"
        
        # Check Flower
        flower_status = await check_service("http://flower:5555/healthcheck")
        if flower_status["status"] == "healthy":
            message += "✅ Flower: Healthy\n"
        else:
            message += f"❌ Flower: {flower_status.get('error', 'Unhealthy')}\n"
        
        message += "\n📊 **System Status**\n"
        message += f"CPU Usage: {cpu_percent:.1f}%\n"
        message += f"Memory Usage: {memory.percent:.1f}%\n"
        message += f"Disk Usage: {disk.percent:.1f}%\n\n"
        
        # Add warnings for high resource usage
        if cpu_percent > 80:
            message += "⚠️ High CPU usage detected!\n"
        if memory.percent > 80:
            message += "⚠️ High memory usage detected!\n"
        if disk.percent > 80:
            message += "⚠️ High disk usage detected!\n"
        
        message += "✨ API is ready to accept connections!"
        
        send_discord_notification.delay(message)
    except Exception as e:
        logger.error(f"Failed to send startup notification: {str(e)}")

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
app.include_router(register.router, prefix="/api", tags=["registration"])
app.include_router(status.router, dependencies=[Depends(get_current_tank)])
app.include_router(commands.router, dependencies=[Depends(get_current_tank)])
app.include_router(config.router, dependencies=[Depends(get_current_tank)])
app.include_router(tanks.router, prefix="/api/tanks", tags=["tanks"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(health.router, tags=["health"])  # No prefix for health check

@app.get("/")
def root():
    return {
        "message": "Aquarium Control API is live",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/metrics")
async def metrics():
    return Response(content=get_metrics(), media_type="text/plain")

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