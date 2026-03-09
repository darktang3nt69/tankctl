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
