import json
from typing import Any, Optional
import asyncio

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

from ..database.config import get_settings

_settings = get_settings()
_redis: Optional["redis.Redis"] = None  # type: ignore
_lock = asyncio.Lock()


async def get_redis():
    global _redis
    if redis is None or not _settings.REDIS_URL:
        raise RuntimeError("Redis client not available or REDIS_URL not set")
    if _redis is None:
        async with _lock:
            if _redis is None:
                _redis = redis.from_url(_settings.REDIS_URL, encoding="utf-8", decode_responses=True)  # type: ignore
    return _redis


async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
    except Exception:
        return None
    data = await r.get(key)  # type: ignore
    if data is None:
        return None
    try:
        return json.loads(data)
    except Exception:
        return data


async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    try:
        r = await get_redis()
    except Exception:
        return
    data = json.dumps(value, default=str)
    await r.set(key, data, ex=ttl_seconds)  # type: ignore


