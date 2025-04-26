"""
Startup tasks for TankCTL.

This module contains tasks that run on startup to verify system health
and send notifications about service status.
"""

import asyncio
import httpx
from celery import Celery
from sqlalchemy.orm import Session
from app.db.session import get_sync_db
from app.tasks.notifications import send_discord_notification
import logging
from typing import Dict, List, Tuple
from app.core.config import settings
import psutil

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "tankctl",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

async def check_service_connection(url: str, timeout: float = 5.0) -> Tuple[bool, Dict]:
    """Check if a service is accessible."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            return response.status_code < 400, response.json() if response.status_code < 400 else {"error": response.text}
    except Exception as e:
        return False, {"error": str(e)}

@celery_app.task
def check_all_services():
    """Check all service connections and send a status report to Discord."""
    services = {
        "App": "http://app:8000/api/health",
        "Prometheus": "http://prometheus:9090/-/healthy",
        "Grafana": "http://grafana:3000/api/health",
        "Flower": "http://flower:5555/healthcheck"
    }
    
    async def check_all():
        results = {}
        for service, url in services.items():
            is_healthy, details = await check_service_connection(url)
            results[service] = (is_healthy, details)
        return results
    
    # Run the async checks
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(check_all())
    
    # Format the message
    message = "🚀 **TankCTL Startup Report**\n\n"
    
    # Add service statuses
    healthy_count = 0
    total_services = len(services)
    
    for service, (is_healthy, details) in results.items():
        status = "✅" if is_healthy else "❌"
        if is_healthy:
            healthy_count += 1
        
        # Add service status
        message += f"{status} **{service}**\n"
        
        # Add details if unhealthy
        if not is_healthy and isinstance(details, dict) and "error" in details:
            message += f"   ↳ Error: {details['error']}\n"
    
    # Add system metrics
    try:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        message += "\n📊 **System Metrics**\n"
        message += f"CPU Usage: {cpu_percent}%\n"
        message += f"Memory Usage: {memory.percent}%\n"
        message += f"Disk Usage: {disk.percent}%\n"
        
        # Add warning indicators for high resource usage
        if cpu_percent > 80:
            message += "⚠️ High CPU usage detected!\n"
        if memory.percent > 80:
            message += "⚠️ High memory usage detected!\n"
        if disk.percent > 80:
            message += "⚠️ High disk usage detected!\n"
            
    except Exception as e:
        message += f"\n❌ Error getting system metrics: {str(e)}\n"
    
    # Add overall health status
    health_percentage = (healthy_count / total_services) * 100
    message += f"\n🏥 **Overall Health**: {health_percentage:.1f}% services healthy\n"
    
    if health_percentage < 100:
        message += "⚠️ Some services are unhealthy! Please check the logs for more details."
    else:
        message += "✨ All services are healthy and running smoothly!"
    
    # Send the notification
    send_discord_notification.delay(message)
    
    return results 