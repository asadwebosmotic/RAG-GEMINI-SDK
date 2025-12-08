import redis
from typing import Optional
from config import settings

_redis_client: Optional[redis.Redis] = None
_in_memory_cache: dict = {}


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client with fallback to None (use in-memory instead)"""
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            _redis_client.ping()
        except Exception:
            _redis_client = None
    
    return _redis_client


def get_cache():
    """Get cache instance (Redis if available, otherwise in-memory dict)"""
    redis_client = get_redis_client()
    if redis_client:
        return redis_client
    return _in_memory_cache


async def close_redis():
    """Close Redis connection on shutdown"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None

