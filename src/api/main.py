"""
TankCtl API - RESTful interface for device management.

FastAPI application with routes for device management, commands, and telemetry.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config.settings import settings
from src.infrastructure.db.database import db
from src.infrastructure.mqtt.handlers import (
    DeviceStatusHandler,
    HeartbeatHandler,
    ReportedStateHandler,
    TelemetryHandler,
)
from src.infrastructure.mqtt.mqtt_client import mqtt_client
from src.infrastructure.scheduler.scheduler import TankCtlScheduler
from src.infrastructure.events.event_publisher import event_publisher
from src.infrastructure.events.event_store import event_store_handler
from src.infrastructure.events.websocket_manager import websocket_manager
from src.services.alert_service import AlertService
from src.services.scheduling_service import SchedulingService
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global scheduler instance
scheduler: TankCtlScheduler | None = None
alert_service: AlertService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Startup:
    - Initialize database
    - Connect to MQTT
    - Start scheduler
    
    Shutdown:
    - Stop scheduler
    - Disconnect MQTT
    - Close database
    """
    # Startup
    logger.info("api_starting")
    
    try:
        # Initialize database
        logger.info("database_initializing")
        db.init_db()
        logger.info("database_ready")
        
        # Initialize event system
        logger.info("event_system_initializing")
        await websocket_manager.start()
        event_publisher.subscribe_all(event_store_handler)
        event_publisher.subscribe_all(websocket_manager.enqueue_event)
        global alert_service
        alert_service = AlertService()
        event_publisher.subscribe("device_offline", alert_service.handle_device_offline_event)
        event_publisher.subscribe("device_online", alert_service.handle_device_online_event)
        event_publisher.subscribe("telemetry_received", alert_service.handle_telemetry_event)
        event_publisher.subscribe("light_state_changed", alert_service.handle_light_state_change_event)
        logger.info("event_system_ready")
        
        # Connect to MQTT
        logger.info("mqtt_connecting")
        mqtt_client.register_handler("telemetry", TelemetryHandler())
        mqtt_client.register_handler("reported", ReportedStateHandler())
        mqtt_client.register_handler("heartbeat", HeartbeatHandler())
        mqtt_client.register_handler("status", DeviceStatusHandler())
        mqtt_client.connect()
        logger.info("mqtt_ready")
        
        # Start scheduler
        logger.info("scheduler_starting")
        global scheduler
        scheduler = TankCtlScheduler()
        scheduler.start()
        logger.info("scheduler_ready")
        
        # Load existing light schedules
        logger.info("loading_schedules")
        session = db.get_session()
        try:
            scheduling_service = SchedulingService(session, scheduler.scheduler)
            scheduling_service.load_all_schedules()
            logger.info("schedules_loaded")
        except Exception as e:
            logger.error("schedule_loading_failed", error=str(e))
            # Don't fail startup if schedule loading fails
        finally:
            session.close()
        
        logger.info("api_ready")
        
    except Exception as e:
        logger.error("api_startup_failed", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("api_shutting_down")
    
    try:
        # Stop scheduler
        if scheduler:
            scheduler.stop()
            logger.info("scheduler_stopped")

        event_publisher.unsubscribe_all(websocket_manager.enqueue_event)
        await websocket_manager.stop()
        logger.info("websocket_manager_shutdown_complete")
        
        # Disconnect MQTT
        mqtt_client.disconnect()
        logger.info("mqtt_disconnected")
        
        # Close database
        db.close()
        logger.info("database_closed")
        
        logger.info("api_shutdown_complete")
        
    except Exception as e:
        logger.error("api_shutdown_error", error=str(e))


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="TankCtl Backend API",
        description="Self-hosted IoT controller for water tank devices",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include route modules
    from src.api.routes import devices, commands, telemetry, health, events, live, push_token

    app.include_router(health.router)
    app.include_router(devices.router)
    app.include_router(commands.router)
    app.include_router(telemetry.router)
    app.include_router(events.router)
    app.include_router(live.router)
    app.include_router(push_token.router)
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        debug=settings.api.debug,
    )
