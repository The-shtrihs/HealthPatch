import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_pool: aioredis.ConnectionPool | None = None


def create_pool(url: str, max_connections: int = 20) -> aioredis.ConnectionPool:
    return aioredis.ConnectionPool.from_url(
        url,
        max_connections=max_connections,
        decode_responses=True,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        socket_keepalive=True,
        retry_on_timeout=True,
        health_check_interval=30,
    )


def get_redis() -> aioredis.Redis:
    if _pool is None:
        raise RuntimeError("Redis pool is not initialized")
    return aioredis.Redis(connection_pool=_pool)


async def close_pool() -> None:
    if _pool is not None:
        await _pool.disconnect()
        logger.info("Redis pool disconnected")

async def register_redis(settings) -> None:
    global _pool
    _pool = create_pool(
    url=settings.redis_url,
    max_connections=settings.redis_max_connections,
    )
    redis = get_redis()
    try:
        pong = await redis.ping()
        logger.info(f"Connected to Redis, ping response: {pong}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
