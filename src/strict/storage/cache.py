from typing import Any
import json
import redis.asyncio as redis
import threading
from strict.config import settings


class CacheManager:
    """Async Redis Cache Manager."""

    def __init__(self):
        self.redis = redis.from_url(
            settings.redis_url, encoding="utf-8", decode_responses=True
        )

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value is not None:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache with consistent JSON serialization."""
        # Always JSON-encode for consistency
        value = json.dumps(value)
        await self.redis.set(key, value, ex=ttl)

    async def close(self):
        """Close connection."""
        await self.redis.close()


# Thread-safe lazy initialization
_cache: CacheManager | None = None
_cache_lock = threading.Lock()


def get_cache() -> CacheManager:
    """Get or create the cache manager singleton (thread-safe)."""
    global _cache
    if _cache is None:
        with _cache_lock:
            # Double-checked locking
            if _cache is None:
                _cache = CacheManager()
    return _cache
