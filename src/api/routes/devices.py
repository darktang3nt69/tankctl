"""
Device Routes - Device management endpoints.

GET /devices - List all devices
GET /devices/{device_id} - Get device status
GET /devices/{device_id}/shadow - Get device shadow state
POST /devices - Register new device
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from src.api.schemas import (
    DeviceResponse,
    DeviceShadowResponse,
    DeviceRegisterRequest,
    DeviceShadowUpdateRequest,
)
from src.infrastructure.db.database import db
from src.services.device_service import DeviceService
from src.services.shadow_service import ShadowService
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
                created_at=d.created_at.isoformat() if d.created_at else None,
                last_seen=d.last_seen.isoformat() if d.last_seen else None,
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
            created_at=device.created_at.isoformat() if device.created_at else None,
            last_seen=device.last_seen.isoformat() if device.last_seen else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_device_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=DeviceResponse, status_code=201)
def register_device(request: DeviceRegisterRequest, session: Session = Depends(get_db)):
    """
    Register a new device.
    
    Args:
        request: Device registration request
    
    Returns:
        Registered device information
    """
    try:
        logger.info("registering_device", device_id=request.device_id)
        
        device_service = DeviceService(session)
        device = device_service.register_device(
            device_id=request.device_id,
            device_secret=request.device_secret,
        )
        
        logger.info("device_registered", device_id=device.device_id)
        
        return DeviceResponse(
            device_id=device.device_id,
            status=device.status,
            firmware_version=device.firmware_version,
            created_at=device.created_at.isoformat() if device.created_at else None,
            last_seen=device.last_seen.isoformat() if device.last_seen else None,
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
