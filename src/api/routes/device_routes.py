"""
Device API routes for TankCtl.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from api.schemas import (
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceShadowResponse,
    DeviceShadowUpdateRequest,
    DeviceMetadataUpdateRequest,
    DeviceDetailResponse,
    LightScheduleRequest,
    LightScheduleResponse,
    WaterScheduleRequest,
    WaterScheduleResponse,
)
from infrastructure.db.database import db
from services.device_service import DeviceService
from services.shadow_service import ShadowService
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/devices", tags=["devices"])


def get_db():
    """Get database session."""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


@router.post("/register", response_model=DeviceResponse)
def register_device(
    request: DeviceRegisterRequest,
    session: Session = Depends(get_db),
):
    """Register a new device."""
    try:
        service = DeviceService(session)
        device = service.register_device(request.device_id, request.device_secret)

        return DeviceResponse(
            device_id=device.device_id,
            status=device.status,
            firmware_version=device.firmware_version,
            created_at=device.created_at.isoformat() if device.created_at else None,
            last_seen=device.last_seen.isoformat() if device.last_seen else None,
            uptime_ms=device.uptime_ms,
            rssi=device.rssi,
            wifi_status=device.wifi_status,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("device_registration_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, session: Session = Depends(get_db)):
    """Get device by ID."""
    try:
        service = DeviceService(session)
        device = service.get_device(device_id)

        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

        return DeviceResponse(
            device_id=device.device_id,
            status=device.status,
            firmware_version=device.firmware_version,
            created_at=device.created_at.isoformat() if device.created_at else None,
            last_seen=device.last_seen.isoformat() if device.last_seen else None,
            uptime_ms=device.uptime_ms,
            rssi=device.rssi,
            wifi_status=device.wifi_status,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_device_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=list[DeviceResponse])
def list_devices(session: Session = Depends(get_db)):
    """List all devices."""
    try:
        service = DeviceService(session)
        devices = service.get_all_devices()

        return [
            DeviceResponse(
                device_id=d.device_id,
                status=d.status,
                firmware_version=d.firmware_version,
                created_at=d.created_at.isoformat() if d.created_at else None,
                last_seen=d.last_seen.isoformat() if d.last_seen else None,
                uptime_ms=d.uptime_ms,
                rssi=d.rssi,
                wifi_status=d.wifi_status,
            )
            for d in devices
        ]
    except Exception as e:
        logger.error("list_devices_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/shadow", response_model=DeviceShadowResponse)
def get_device_shadow(device_id: str, session: Session = Depends(get_db)):
    """Get device shadow state."""
    try:
        service = DeviceService(session)
        shadow = service.get_device_shadow(device_id)

        if not shadow:
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
def update_device_shadow(
    device_id: str,
    request: DeviceShadowUpdateRequest,
    session: Session = Depends(get_db),
):
    """Update device shadow desired state."""
    try:
        service = ShadowService(session)
        shadow = service.set_desired_state(device_id, request.desired)

        if not shadow:
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
        logger.error("update_shadow_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device_metadata(
    device_id: str,
    request,
    session: Session = Depends(get_db),
):
    """Update device metadata (name, location, icon, description, thresholds)."""
    try:
        service = DeviceService(session)
        device = service.update_device_metadata(device_id, request)

        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

        return DeviceResponse(
            device_id=device.device_id,
            device_name=device.device_name,
            location=device.location,
            icon_type=device.icon_type,
            description=device.description,
            status=device.status,
            firmware_version=device.firmware_version,
            created_at=device.created_at.isoformat() if device.created_at else None,
            last_seen=device.last_seen.isoformat() if device.last_seen else None,
            uptime_ms=device.uptime_ms,
            rssi=device.rssi,
            wifi_status=device.wifi_status,
            temp_threshold_low=device.temp_threshold_low,
            temp_threshold_high=device.temp_threshold_high,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_device_metadata_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/detail", response_model=DeviceDetailResponse)
def get_device_detail(
    device_id: str,
    session: Session = Depends(get_db),
):
    """Get complete device detail with all settings and schedules."""
    try:
        service = DeviceService(session)
        device_detail = service.get_device_detail(device_id)

        if not device_detail:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

        return device_detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_device_detail_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


# Light Schedule Endpoints

@router.post("/{device_id}/schedule/light", response_model=LightScheduleResponse)
def create_or_update_light_schedule(
    device_id: str,
    request,
    session: Session = Depends(get_db),
):
    """Create or update light schedule for device."""
    try:
        service = DeviceService(session)
        schedule = service.set_light_schedule(device_id, request)

        if not schedule:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

        return LightScheduleResponse(
            id=schedule.id,
            device_id=schedule.device_id,
            enabled=schedule.enabled,
            start_time=str(schedule.start_time),
            end_time=str(schedule.end_time),
            created_at=schedule.created_at.isoformat() if schedule.created_at else None,
            updated_at=schedule.updated_at.isoformat() if schedule.updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_light_schedule_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/schedule/light", response_model=LightScheduleResponse)
def get_light_schedule(
    device_id: str,
    session: Session = Depends(get_db),
):
    """Get light schedule for device."""
    try:
        service = DeviceService(session)
        schedule = service.get_light_schedule(device_id)

        if not schedule:
            raise HTTPException(status_code=404, detail=f"No light schedule for device {device_id}")

        return LightScheduleResponse(
            id=schedule.id,
            device_id=schedule.device_id,
            enabled=schedule.enabled,
            start_time=str(schedule.start_time),
            end_time=str(schedule.end_time),
            created_at=schedule.created_at.isoformat() if schedule.created_at else None,
            updated_at=schedule.updated_at.isoformat() if schedule.updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_light_schedule_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


# Water Schedule Endpoints

@router.post("/{device_id}/schedule/water", response_model=WaterScheduleResponse)
def create_water_schedule(
    device_id: str,
    request,
    session: Session = Depends(get_db),
):
    """Create water change schedule for device."""
    try:
        service = DeviceService(session)
        schedule = service.create_water_schedule(device_id, request)

        if not schedule:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

        return WaterScheduleResponse(
            id=schedule.id,
            device_id=schedule.device_id,
            schedule_type=schedule.schedule_type,
            day_of_week=schedule.day_of_week,
            schedule_date=schedule.schedule_date,
            schedule_time=str(schedule.schedule_time),
            notes=schedule.notes,
            completed=schedule.completed,
            created_at=schedule.created_at.isoformat() if schedule.created_at else None,
            updated_at=schedule.updated_at.isoformat() if schedule.updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_water_schedule_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/schedule/water", response_model=list[WaterScheduleResponse])
def get_water_schedules(
    device_id: str,
    session: Session = Depends(get_db),
):
    """Get all water schedules for device."""
    try:
        service = DeviceService(session)
        schedules = service.get_water_schedules(device_id)

        return [
            WaterScheduleResponse(
                id=schedule.id,
                device_id=schedule.device_id,
                schedule_type=schedule.schedule_type,
                day_of_week=schedule.day_of_week,
                schedule_date=schedule.schedule_date,
                schedule_time=str(schedule.schedule_time),
                notes=schedule.notes,
                completed=schedule.completed,
                created_at=schedule.created_at.isoformat() if schedule.created_at else None,
                updated_at=schedule.updated_at.isoformat() if schedule.updated_at else None,
            )
            for schedule in schedules
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_water_schedules_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{device_id}/schedule/water/{schedule_id}")
def delete_water_schedule(
    device_id: str,
    schedule_id: int,
    session: Session = Depends(get_db),
):
    """Delete water change schedule."""
    try:
        service = DeviceService(session)
        success = service.delete_water_schedule(device_id, schedule_id)

        if not success:
            raise HTTPException(status_code=404, detail="Water schedule not found")

        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_water_schedule_error", schedule_id=schedule_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
