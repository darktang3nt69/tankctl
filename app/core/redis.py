"""
Redis client configuration for TankCTL.

This module provides a Redis client instance for use throughout the application.
"""

import redis
from app.core.config import settings

# Create Redis client instance
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True
) 