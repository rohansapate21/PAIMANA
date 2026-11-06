"""
SIH 2026 — PS26103 | Redis Cache Helper with Fallback
=====================================================
Provides async caching for high-volume dashboard analytics endpoints.
Gracefully falls back to an in-memory TTL dictionary cache if Redis is unavailable.
"""

import json
import time
from typing import Optional, Any, Dict
from loguru import logger

from backend.app.core.config import settings

# In-memory fallback cache store: key -> (value, expiry_timestamp)
_MEMORY_CACHE: Dict[str, tuple[str, float]] = {}
_REDIS_CLIENT = None
_REDIS_CHECKED = False


async def get_redis_client():
    """Lazily initializes the redis client, returning None if unavailable."""
    global _REDIS_CLIENT, _REDIS_CHECKED
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT
    if _REDIS_CHECKED:
        return None

    try:
        import redis.asyncio as aioredis
        redis_url = settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await client.ping()
        _REDIS_CLIENT = client
        logger.info("Connected to Redis cache successfully.")
        return _REDIS_CLIENT
    except Exception as e:
        logger.warning(f"Redis unavailable ({e}). Using in-memory fallback cache.")
        _REDIS_CHECKED = True
        return None


async def get_cache(key: str) -> Optional[Any]:
    """Retrieve cached data by key."""
    client = await get_redis_client()
    if client:
        try:
            val = await client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")

    # Fallback in-memory
    entry = _MEMORY_CACHE.get(key)
    if entry:
        raw_val, expiry = entry
        if time.time() < expiry:
            return json.loads(raw_val)
        else:
            del _MEMORY_CACHE[key]
    return None


async def set_cache(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Store data in cache with TTL (default 300s / 5 minutes)."""
    serialized = json.dumps(value, default=str)
    client = await get_redis_client()
    if client:
        try:
            await client.set(key, serialized, ex=ttl_seconds)
            return
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")

    # Fallback in-memory
    _MEMORY_CACHE[key] = (serialized, time.time() + ttl_seconds)


async def invalidate_cache(key_or_prefix: str) -> None:
    """Evict a specific cache key or prefix."""
    client = await get_redis_client()
    if client:
        try:
            keys = await client.keys(f"{key_or_prefix}*")
            if keys:
                await client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis invalidate failed: {e}")

    keys_to_delete = [k for k in _MEMORY_CACHE if k.startswith(key_or_prefix)]
    for k in keys_to_delete:
        _MEMORY_CACHE.pop(k, None)

