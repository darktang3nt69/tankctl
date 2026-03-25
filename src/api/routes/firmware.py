"""
Firmware management API routes.

Endpoints:
- POST /firmware/upload - Upload new firmware
- GET /firmware/download/{version} - Download firmware binary  
- POST /devices/{device_id}/firmware/update - Trigger device firmware update
- GET /firmware/releases - List all firmware releases
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from src.api.schemas import DeviceResponse
from src.infrastructure.db.database import get_db
from src.services.firmware_service import FirmwareService
from src.services.device_service import DeviceService
from src.infrastructure.scheduler.scheduler import get_scheduler
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/firmware", tags=["firmware"])


@router.post("/upload")
def upload_firmware(
    file: UploadFile = File(...),
    version: str = Query(..., description="Semantic version (e.g., 2.0.0)"),
    platform: str = Query(default="esp32", description="Target platform: esp32, arduino"),
    release_notes: str = Query(default="", description="Release notes/changelog"),
    session: Session = Depends(get_db),
):
    """
    Upload a new firmware release.
    
    Args:
        file: Firmware binary file
        version: Semantic version string
        platform: Target platform (esp32, arduino)
        release_notes: Release notes
    
    Returns:
        Firmware release metadata
    """
    try:
        logger.info("firmware_upload_request", filename=file.filename, version=version, platform=platform)
        
        # Read file data
        file_data = file.file.read()
        if not file_data:
            raise HTTPException(status_code=400, detail="Empty file")
        
        logger.info("firmware_upload_data_read", size=len(file_data))
        
        # Upload via service
        firmware_service = FirmwareService(session)
        release = firmware_service.upload_firmware(
            file_data=file_data,
            version=version,
            platform=platform,
            release_notes=release_notes or None,
        )
        
        logger.info("firmware_upload_success", version=version)
        
        return {
            "id": release.id,
            "version": release.version,
            "filename": release.filename,
            "file_size": release.file_size,
            "checksum": release.checksum,
            "platform": release.platform,
            "release_notes": release.release_notes,
            "created_at": release.created_at.isoformat() if release.created_at else None,
        }
        
    except Exception as e:
        logger.error("firmware_upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/download/{version}")
def download_firmware(version: str, session: Session = Depends(get_db)):
    """
    Download firmware binary by version.
    
    This endpoint is called by devices during OTA updates.
    
    Args:
        version: Firmware version to download
    
    Returns:
        Binary firmware file
    """
    try:
        logger.debug("firmware_download_request", version=version)
        
        firmware_service = FirmwareService(session)
        file_data = firmware_service.get_firmware_file(version)
        
        if not file_data:
            raise HTTPException(status_code=404, detail=f"Firmware version {version} not found")
        
        logger.info("firmware_download_served", version=version, size=len(file_data))
        
        return {
            "data": file_data,
            "content_type": "application/octet-stream",
            "filename": f"firmware-{version}.bin",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("firmware_download_failed", version=version, error=str(e))
        raise HTTPException(status_code=500, detail="Download failed")


@router.get("/releases")
def list_firmware_releases(
    platform: str = Query(default="esp32"),
    session: Session = Depends(get_db),
):
    """
    List all firmware releases for a platform.
    
    Args:
        platform: Target platform filter (esp32, arduino)
    
    Returns:
        List of firmware releases
    """
    try:
        logger.debug("firmware_releases_list_request", platform=platform)
        
        firmware_service = FirmwareService(session)
        releases = firmware_service.release_repo.get_all(platform=platform)
        
        return [
            {
                "id": r.id,
                "version": r.version,
                "filename": r.filename,
                "file_size": r.file_size,
                "checksum": r.checksum,
                "platform": r.platform,
                "release_notes": r.release_notes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in releases
        ]
        
    except Exception as e:
        logger.error("firmware_releases_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list releases")


@router.post("/devices/{device_id}/update")
def trigger_device_firmware_update(
    device_id: str,
    version: str = Query(..., description="Firmware version to deploy"),
    session: Session = Depends(get_db),
):
    """
    Trigger firmware update for a device.
    
    Sends MQTT command to device with firmware download URL.
    
    Args:
        device_id: Device ID
        version: Firmware version to deploy
    
    Returns:
        Deployment status
    """
    try:
        logger.info("firmware_deploy_request", device_id=device_id, version=version)
        
        # Verify device exists
        device_service = DeviceService(session)
        device = device_service.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Get firmware service
        firmware_service = FirmwareService(session)
        
        # Get release info
        release = firmware_service.release_repo.get_by_version(version)
        if not release:
            raise HTTPException(status_code=404, detail=f"Firmware version {version} not found")
        
        # Deploy to device
        deployment = firmware_service.deploy_to_device(
            device_id=device_id,
            version=version,
            release_id=release.id,
        )
        
        logger.info("firmware_deploy_triggered", device_id=device_id, version=version)
        
        return {
            "id": deployment.id,
            "device_id": deployment.device_id,
            "release_id": deployment.release_id,
            "status": deployment.status,
            "command_version": deployment.command_version,
            "attempted_at": deployment.attempted_at.isoformat() if deployment.attempted_at else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("firmware_deploy_failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Deploy failed: {str(e)}")
