"""
Health check endpoints for TankCTL.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_sync_db
from app.core.redis import redis_client
import psutil
import httpx
import asyncio
from typing import Dict, Any

router = APIRouter()

def format_bytes(bytes_value: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

async def check_service(url: str) -> Dict[str, Any]:
    """Check if a service is accessible."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            return {
                "status": "healthy" if response.status_code < 400 else "unhealthy",
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/health")
async def health_check():
    """Check the health of the application and its dependencies."""
    health_info = {
        "status": "healthy",
        "services": {},
        "system": {}
    }
    
    # Check database connection
    db: Session = next(get_sync_db())
    try:
        db.execute(text("SELECT 1"))
        health_info["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_info["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_info["status"] = "unhealthy"
    finally:
        db.close()
    
    # Check Redis connection
    try:
        redis_client.ping()
        health_info["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_info["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_info["status"] = "unhealthy"
    
    # Check Celery worker
    try:
        celery_workers = redis_client.llen("celery")
        if celery_workers > 0:
            health_info["services"]["celery"] = {"status": "healthy"}
        else:
            health_info["services"]["celery"] = {"status": "unhealthy", "error": "No workers found"}
            health_info["status"] = "unhealthy"
    except Exception as e:
        health_info["services"]["celery"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_info["status"] = "unhealthy"
    
    # Check Flower
    flower_status = await check_service("http://flower:5555/healthcheck")
    health_info["services"]["flower"] = flower_status
    if flower_status["status"] == "unhealthy":
        health_info["status"] = "unhealthy"
    
    # Add system metrics
    try:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_info["system"] = {
            "cpu": {
                "usage_percent": f"{cpu_percent:.1f}%"
            },
            "memory": {
                "total": format_bytes(memory.total),
                "available": format_bytes(memory.available),
                "used_percent": f"{memory.percent:.1f}%"
            },
            "disk": {
                "total": format_bytes(disk.total),
                "free": format_bytes(disk.free),
                "used_percent": f"{disk.percent:.1f}%"
            }
        }
    except Exception as e:
        health_info["system"] = {"error": str(e)}
    
    if health_info["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_info)
    
    return health_info 