from redis.asyncio import ConnectionPool, Redis
from app.core.config import settings

_redis_pool: ConnectionPool | None = None

async def get_redis_pool() -> Redis:
    """
    Returns a Redis client from a connection pool.
    Initializes the pool if it doesn't exist.
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8"
        )
    return Redis(connection_pool=_redis_pool) 