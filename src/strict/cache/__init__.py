"""Enhanced Caching Layer.

Provides decorators and utilities for caching with Redis.
"""

from strict.cache.decorators import CacheStats, cache_result, cached, cache_stats

__all__ = [
    "cached",
    "cache_result",
    "CacheStats",
    "cache_stats",
]
