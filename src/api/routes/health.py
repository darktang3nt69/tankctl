"""
Health Routes - Health check endpoints.

GET / - API health status
"""

from fastapi import APIRouter

from src.api.schemas import HealthResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    logger.debug("health_check")
    
    return HealthResponse(
        status="healthy",
        message="TankCtl API is running",
    )


@router.get("/", response_model=HealthResponse)
def root():
    """
    Root endpoint.
    
    Returns:
        API information
    """
    return HealthResponse(
        status="healthy",
        message="TankCtl Backend API",
    )
