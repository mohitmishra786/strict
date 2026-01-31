"""Enhanced Caching Layer with Redis.

Provides decorators and utilities for caching function results,
with support for TTL, cache invalidation, and statistics.
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import logging
import threading
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from strict.storage.cache import get_cache

if TYPE_CHECKING:
    from collections.abc import Coroutine

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheStats:
    """Cache statistics tracker with thread-safety."""

    def __init__(self) -> None:
        """Initialize cache stats with lock for thread safety."""
        self._lock = threading.Lock()
        self.hits: int = 0
        self.misses: int = 0
        self.errors: int = 0

    def record_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self.hits += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self.misses += 1

    def record_error(self) -> None:
        """Record a cache error."""
        with self._lock:
            self.errors += 1

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, int | float]:
        """Convert stats to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": self.hit_rate,
        }


# Global cache stats instance
cache_stats = CacheStats()


def _generate_cache_key(
    func_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    key_prefix: str | None = None,
) -> str:
    """Generate a cache key from function arguments.

    Args:
        func_name: Name of the function being cached.
        args: Positional arguments.
        kwargs: Keyword arguments.
        key_prefix: Optional prefix for the cache key.

    Returns:
        A cache key string.
    """
    # Create a deterministic hash of the arguments
    key_parts = {
        "args": str(args),
        "kwargs": str(sorted(kwargs.items())),
    }

    key_hash = hashlib.sha256(
        json.dumps(key_parts, sort_keys=True).encode()
    ).hexdigest()[:16]

    prefix = key_prefix or f"cache:{func_name}"
    return f"{prefix}:{key_hash}"


def cached(
    ttl: int = 3600,
    key_prefix: str | None = None,
    skip_args: tuple[str, ...] = (),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to cache function results in Redis.

    Args:
        ttl: Time-to-live in seconds (default: 1 hour).
        key_prefix: Optional prefix for cache keys.
        skip_args: Argument names to exclude from cache key generation.

    Returns:
        Decorated function with caching.

    Example:
        @cached(ttl=600, key_prefix="user_data")
        async def get_user(user_id: int) -> User:
            return await db.fetch_user(user_id)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            # Filter out skipped arguments from key generation
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in skip_args}

            cache_key = _generate_cache_key(
                func.__name__, args, filtered_kwargs, key_prefix
            )

            try:
                # Try to get from cache
                cached_value = await get_cache().get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    cache_stats.record_hit()
                    return cached_value

                # Cache miss - call the function
                logger.debug(f"Cache miss for key: {cache_key}")
                cache_stats.record_miss()
                result = await func(*args, **kwargs)

                # Store in cache
                await get_cache().set(cache_key, result, ttl)
                return result

            except Exception as e:
                logger.warning(f"Cache error: {e}, falling back to function call")
                cache_stats.record_error()
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            # Filter out skipped arguments from key generation
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in skip_args}

            cache_key = _generate_cache_key(
                func.__name__, args, filtered_kwargs, key_prefix
            )

            try:
                # Try to get from cache (synchronous)
                cached_value = asyncio.run(get_cache().get(cache_key))

                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    cache_stats.record_hit()
                    return cached_value

                # Cache miss - call the function
                logger.debug(f"Cache miss for key: {cache_key}")
                cache_stats.record_miss()
                result = func(*args, **kwargs)

                # Store in cache
                asyncio.run(get_cache().set(cache_key, result, ttl))
                return result

            except Exception as e:
                logger.warning(f"Cache error: {e}, falling back to function call")
                cache_stats.record_error()
                return func(*args, **kwargs)

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def cache_result(
    ttl: int = 3600,
    key: str | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Simple decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds.
        key: Optional cache key (auto-generated if not provided).

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache_key = key or f"result:{func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                cached_value = await get_cache().get(cache_key)
                if cached_value is not None:
                    cache_stats.record_hit()
                    return cached_value

                result = await func(*args, **kwargs)
                cache_stats.record_miss()
                await get_cache().set(cache_key, result, ttl)
                return result

            except Exception:
                cache_stats.record_error()
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                cached_value = asyncio.run(get_cache().get(cache_key))

                if cached_value is not None:
                    cache_stats.record_hit()
                    return cached_value

                result = func(*args, **kwargs)
                cache_stats.record_miss()
                asyncio.run(get_cache().set(cache_key, result, ttl))
                return result

            except Exception:
                cache_stats.record_error()
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


class CacheStats:
    """Cache statistics tracker."""

    def __init__(self) -> None:
        """Initialize cache stats."""
        self.hits: int = 0
        self.misses: int = 0
        self.errors: int = 0

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hits += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        self.misses += 1

    def record_error(self) -> None:
        """Record a cache error."""
        self.errors += 1

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, int | float]:
        """Convert stats to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": self.hit_rate,
        }


# Global cache stats instance
cache_stats = CacheStats()
