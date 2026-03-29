"""
DEPRECATED: This file has been removed as part of dead code cleanup.
Use src/api/routes/health.py instead.
"""


from api.schemas import HealthResponse
from infrastructure.mqtt.mqtt_client import mqtt_client
from infrastructure.db.database import db
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    mqtt_status = "connected" if mqtt_client.is_connected else "disconnected"
    status = "healthy" if mqtt_client.is_connected else "degraded"

    return HealthResponse(
        status=status,
        message=f"Backend is {status}. MQTT: {mqtt_status}",
    )
