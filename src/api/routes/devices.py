"""
Device Routes - Device management endpoints.

GET /devices - List all devices
GET /devices/{device_id} - Get device status
GET /devices/{device_id}/shadow - Get device shadow state
POST /devices - Register new device
POST /devices/{device_id}/schedule - Create or update light schedule
GET /devices/{device_id}/schedule - Get light schedule
DELETE /devices/{device_id}/schedule - Delete light schedule
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import time as dt_time

from src.api.schemas import (
    DeviceResponse,
    DeviceShadowResponse,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    DeviceShadowUpdateRequest,
    ScheduleRequest,
    ScheduleResponse,
)
from src.infrastructure.db.database import db
from src.services.device_service import DeviceService
from src.services.shadow_service import ShadowService
from src.services.scheduling_service import SchedulingService
from src.utils.datetime_utils import isoformat_in_app_timezone
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/devices", tags=["devices"])


def get_db():
    """Dependency: Get database session."""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def get_scheduler():
    """Dependency: Get scheduler instance."""
    from src.api.main import scheduler
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    return scheduler


@router.get("", response_model=dict)
def list_devices(session: Session = Depends(get_db)):
    """
    List all registered devices.
    
    Returns:
        List of devices with status and metadata
    """
    try:
        logger.debug("listing_devices")
        
        device_service = DeviceService(session)
        devices = device_service.get_all_devices()
        
        device_list = [
            DeviceResponse(
                device_id=d.device_id,
                status=d.status,
                firmware_version=d.firmware_version,
                created_at=isoformat_in_app_timezone(d.created_at),
                last_seen=isoformat_in_app_timezone(d.last_seen),
                uptime_ms=d.uptime_ms,
                rssi=d.rssi,
                wifi_status=d.wifi_status,
            )
            for d in devices
        ]
        
        logger.info("devices_listed", count=len(device_list))
        
        return {
            "count": len(device_list),
            "devices": device_list
        }
        
    except Exception as e:
        logger.error("list_devices_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, session: Session = Depends(get_db)):
    """
    Get device status and information.
    
    Args:
        device_id: Device identifier
    
    Returns:
        Device information
    """
    try:
        logger.debug("getting_device", device_id=device_id)
        
        device_service = DeviceService(session)
        device = device_service.get_device(device_id)
        
        if not device:
            logger.warning("device_not_found", device_id=device_id)
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        return DeviceResponse(
            device_id=device.device_id,
            status=device.status,
            firmware_version=device.firmware_version,
            created_at=isoformat_in_app_timezone(device.created_at),
            last_seen=isoformat_in_app_timezone(device.last_seen),
            uptime_ms=device.uptime_ms,
            rssi=device.rssi,
            wifi_status=device.wifi_status,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_device_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=DeviceRegisterResponse, status_code=201)
def register_device(request: DeviceRegisterRequest, session: Session = Depends(get_db)):
    """
    Register a new device.
    
    Backend auto-generates a secure device_secret that must be provisioned into the device firmware.
    
    Args:
        request: Device registration request (device_id only)
    
    Returns:
        Registered device with auto-generated device_secret
    """
    try:
        logger.info("registering_device", device_id=request.device_id)
        
        device_service = DeviceService(session)
        device = device_service.register_device(
            device_id=request.device_id,
        )
        
        logger.info("device_registered", device_id=device.device_id)
        
        return DeviceRegisterResponse(
            device_id=device.device_id,
            device_secret=device.device_secret,
            status=device.status,
            created_at=isoformat_in_app_timezone(device.created_at),
        )
        
    except ValueError as e:
        logger.warning("device_registration_failed", device_id=request.device_id, reason=str(e))
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("register_device_error", device_id=request.device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/shadow", response_model=DeviceShadowResponse)
def get_shadow(device_id: str, session: Session = Depends(get_db)):
    """
    Get device shadow state (desired and reported).
    
    Args:
        device_id: Device identifier
    
    Returns:
        Device shadow state
    """
    try:
        logger.debug("getting_shadow", device_id=device_id)
        
        device_service = DeviceService(session)
        shadow = device_service.get_device_shadow(device_id)
        
        if not shadow:
            logger.warning("shadow_not_found", device_id=device_id)
            raise HTTPException(status_code=404, detail=f"Shadow for device {device_id} not found")
        
        return DeviceShadowResponse(
            device_id=shadow.device_id,
            desired=shadow.desired,
            reported=shadow.reported,
            version=shadow.version,
            synchronized=shadow.is_synchronized(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_shadow_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{device_id}/shadow", response_model=DeviceShadowResponse)
def update_shadow(device_id: str, request: DeviceShadowUpdateRequest, session: Session = Depends(get_db)):
    """
    Update device shadow desired state.
    
    Args:
        device_id: Device identifier
        request: Shadow update request with "desired" state
    
    Returns:
        Updated shadow state
    """
    try:
        logger.info("updating_shadow", device_id=device_id)
        
        shadow_service = ShadowService(session)
        shadow = shadow_service.set_desired_state(device_id, request.desired)
        
        if not shadow:
            logger.warning("shadow_not_found", device_id=device_id)
            raise HTTPException(status_code=404, detail=f"Shadow for device {device_id} not found")
        
        logger.info("shadow_updated", device_id=device_id, version=shadow.version)
        
        return DeviceShadowResponse(
            device_id=shadow.device_id,
            desired=shadow.desired,
            reported=shadow.reported,
            version=shadow.version,
            synchronized=shadow.is_synchronized(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_shadow_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Light Schedule Endpoints
# ============================================================================

@router.post("/{device_id}/schedule", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    device_id: str,
    request: ScheduleRequest,
    session: Session = Depends(get_db),
    scheduler = Depends(get_scheduler)
):
    """
    Create or update light schedule for a device.
    
    Args:
        device_id: Device identifier
        request: Schedule with on_time and off_time in HH:MM format
    
    Returns:
        Created or updated schedule
    """
    try:
        logger.info("creating_schedule", device_id=device_id, on_time=request.on_time, off_time=request.off_time)
        
        # Verify device exists
        device_service = DeviceService(session)
        device = device_service.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Parse time strings to time objects
        try:
            on_hour, on_minute = map(int, request.on_time.split(':'))
            off_hour, off_minute = map(int, request.off_time.split(':'))
            on_time = dt_time(on_hour, on_minute)
            off_time = dt_time(off_hour, off_minute)
        except ValueError as e:
            logger.error("invalid_time_format", device_id=device_id, error=str(e))
            raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
        
        # Create schedule
        scheduling_service = SchedulingService(session, scheduler.scheduler)
        schedule = scheduling_service.create_schedule(device_id, on_time, off_time, request.enabled)
        
        logger.info("schedule_created", device_id=device_id, on_time=request.on_time, off_time=request.off_time)
        
        return ScheduleResponse(
            device_id=schedule.device_id,
            on_time=schedule.on_time.strftime("%H:%M"),
            off_time=schedule.off_time.strftime("%H:%M"),
            enabled=schedule.enabled,
            created_at=isoformat_in_app_timezone(schedule.created_at),
            updated_at=isoformat_in_app_timezone(schedule.updated_at),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_schedule_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/schedule", response_model=ScheduleResponse)
def get_schedule(
    device_id: str,
    session: Session = Depends(get_db),
    scheduler = Depends(get_scheduler)
):
    """
    Get light schedule for a device.
    
    Args:
        device_id: Device identifier
    
    Returns:
        Schedule details or 404 if not found
    """
    try:
        logger.debug("getting_schedule", device_id=device_id)
        
        scheduling_service = SchedulingService(session, scheduler.scheduler)
        schedule = scheduling_service.get_schedule(device_id)
        
        if not schedule:
            logger.warning("schedule_not_found", device_id=device_id)
            raise HTTPException(status_code=404, detail=f"Schedule for device {device_id} not found")
        
        return ScheduleResponse(
            device_id=schedule.device_id,
            on_time=schedule.on_time.strftime("%H:%M"),
            off_time=schedule.off_time.strftime("%H:%M"),
            enabled=schedule.enabled,
            created_at=isoformat_in_app_timezone(schedule.created_at),
            updated_at=isoformat_in_app_timezone(schedule.updated_at),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_schedule_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{device_id}/schedule", status_code=204)
def delete_schedule(
    device_id: str,
    session: Session = Depends(get_db),
    scheduler = Depends(get_scheduler)
):
    """
    Delete light schedule for a device.
    
    Args:
        device_id: Device identifier
    
    Returns:
        204 No Content on success
    """
    try:
        logger.info("deleting_schedule", device_id=device_id)
        
        scheduling_service = SchedulingService(session, scheduler.scheduler)
        deleted = scheduling_service.delete_schedule(device_id)
        
        if not deleted:
            logger.warning("schedule_not_found", device_id=device_id)
            raise HTTPException(status_code=404, detail=f"Schedule for device {device_id} not found")
        
        logger.info("schedule_deleted", device_id=device_id)
        
        # No content to return (204 status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_schedule_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
