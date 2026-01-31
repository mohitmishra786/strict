from typing import Any
import json
import redis.asyncio as redis
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
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache."""
        if not isinstance(value, (str, int, float, bool)):
            value = json.dumps(value)
        await self.redis.set(key, value, ex=ttl)

    async def close(self):
        """Close connection."""
        await self.redis.close()


cache = CacheManager()
