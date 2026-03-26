"""
Service for managing firmware releases and deployments.
"""

import hashlib
import os
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.domain.firmware import FirmwareRelease, FirmwareDeployment
from src.repository.firmware_repository import FirmwareReleaseRepository, FirmwareDeploymentRepository
from src.services.command_service import CommandService
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Configure firmware storage directory
FIRMWARE_STORAGE_DIR = os.getenv("FIRMWARE_STORAGE_DIR", "./firmware_releases")


def _ensure_firmware_dir():
    """Create firmware storage directory if it doesn't exist."""
    try:
        os.makedirs(FIRMWARE_STORAGE_DIR, exist_ok=True)
    except PermissionError as e:
        logger.error(f"Failed to create firmware storage directory: {e}")
        raise


class FirmwareService:
    """Service for firmware management."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session
        self.release_repo = FirmwareReleaseRepository(session) if session else None
        self.deployment_repo = FirmwareDeploymentRepository(session) if session else None
        self.command_service = CommandService(session) if session else None

    def upload_firmware(
        self,
        file_data: bytes,
        version: str,
        platform: str = "esp32",
        release_notes: Optional[str] = None,
    ) -> FirmwareRelease:
        """
        Upload a new firmware release.

        Args:
            file_data: Raw firmware binary data
            version: Semantic version string (e.g., "2.0.0")
            platform: Target platform (esp32, arduino)
            release_notes: Release notes/changelog

        Returns:
            FirmwareRelease object with metadata
        """
        # Ensure firmware storage directory exists
        _ensure_firmware_dir()
        
        logger.info("firmware_upload_started", version=version, platform=platform, size=len(file_data))

        # Calculate file hash
        file_hash = hashlib.sha256(file_data).hexdigest()

        # Create filename: firmware-{platform}-{version}.bin
        filename = f"firmware-{platform}-{version}.bin"
        filepath = os.path.join(FIRMWARE_STORAGE_DIR, filename)

        # Check if already exists
        if os.path.exists(filepath):
            logger.warning("firmware_already_exists", version=version, platform=platform)
            raise Exception(f"Firmware version {version} already exists")

        # Write to disk
        try:
            with open(filepath, "wb") as f:
                f.write(file_data)
            logger.info("firmware_written_to_disk", filepath=filepath, size=len(file_data))
        except Exception as e:
            logger.error("firmware_write_failed", filepath=filepath, error=str(e))
            raise

        # Create release record in database
        release = FirmwareRelease(
            version=version,
            filename=filename,
            file_size=len(file_data),
            checksum=file_hash,
            platform=platform,
            release_notes=release_notes,
        )

        try:
            stored_release = self.release_repo.create(release)
            logger.info(
                "firmware_release_stored",
                version=version,
                checksum=file_hash,
                platform=platform,
            )
            return stored_release
        except Exception as e:
            # Clean up file if db insert fails
            try:
                os.remove(filepath)
            except:
                pass
            logger.error("firmware_store_failed", version=version, error=str(e))
            raise

    def get_download_url(self, release: FirmwareRelease) -> str:
        """
        Get download URL for firmware release.

        Args:
            release: FirmwareRelease object

        Returns:
            Download URL that devices can use
        """
        # Construct URL: /firmware/download/{version}
        base_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")
        return f"{base_url}/firmware/download/{release.version}"

    def deploy_to_device(
        self, device_id: str, version: str, release_id: int
    ) -> FirmwareDeployment:
        """
        Deploy firmware to a device via MQTT command.

        Args:
            device_id: Device ID
            version: Firmware version
            release_id: Release ID in database

        Returns:
            FirmwareDeployment object
        """
        logger.info("firmware_deploy_started", device_id=device_id, version=version)

        # Create deployment record
        deployment = FirmwareDeployment(
            release_id=release_id,
            device_id=device_id,
            status="pending",
            attempted_at=datetime.utcnow(),
        )

        try:
            stored_deployment = self.deployment_repo.create(deployment)
        except Exception as e:
            logger.error("firmware_deployment_create_failed", device_id=device_id, error=str(e))
            raise

        # Get release for download URL
        release = self.release_repo.get_by_version(version)
        if not release:
            logger.error("firmware_release_not_found", version=version)
            raise Exception(f"Firmware version {version} not found")

        download_url = self.get_download_url(release)

        # Send MQTT command to device
        try:
            command_version = self.command_service.send_command(
                device_id=device_id,
                command="update_firmware",
                value="",  # Not used for firmware updates
                version=stored_deployment.id,  # Use deployment ID as version
                metadata={
                    "url": download_url,
                    "version": version,
                    "checksum": release.checksum,
                },
            )

            stored_deployment.command_version = command_version
            logger.info(
                "firmware_deploy_command_sent",
                device_id=device_id,
                version=version,
                url=download_url,
            )

            return stored_deployment

        except Exception as e:
            logger.error("firmware_deploy_command_failed", device_id=device_id, error=str(e))
            self.deployment_repo.update_status(
                stored_deployment.id, "failed", f"Command send failed: {str(e)}"
            )
            raise

    def get_firmware_file(self, version: str) -> Optional[bytes]:
        """
        Get firmware binary data for download.

        Args:
            version: Firmware version

        Returns:
            Binary firmware data, or None if not found
        """
        logger.debug("firmware_download_requested", version=version)

        # Build filepath
        # Try both esp32 and arduino platforms
        for platform in ["esp32", "arduino"]:
            filename = f"firmware-{platform}-{version}.bin"
            filepath = os.path.join(FIRMWARE_STORAGE_DIR, filename)

            if os.path.exists(filepath):
                try:
                    with open(filepath, "rb") as f:
                        data = f.read()
                    logger.info("firmware_downloaded", version=version, size=len(data), platform=platform)
                    return data
                except Exception as e:
                    logger.error("firmware_read_failed", filepath=filepath, error=str(e))
                    return None

        logger.warning("firmware_not_found", version=version)
        return None

    def update_deployment_status(
        self, device_id: str, status: str, error_message: Optional[str] = None
    ) -> None:
        """
        Update deployment status from device feedback (via MQTT).

        Args:
            device_id: Device ID
            status: New status (updating, success, failed)
            error_message: Error message if failed
        """
        deployment = self.deployment_repo.get_by_device(device_id)
        if deployment:
            self.deployment_repo.update_status(deployment.id, status, error_message)
            logger.info(
                "firmware_deployment_status_updated",
                device_id=device_id,
                status=status,
                error=error_message,
            )
