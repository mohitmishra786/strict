"""Tests for enhanced caching layer."""

import asyncio

from unittest.mock import AsyncMock, patch
import pytest

from strict.cache import cached, cache_result, cache_stats
from strict.storage.cache import get_cache


@pytest.fixture(autouse=True)
def reset_cache_stats():
    """Reset global cache stats before each test."""
    cache_stats.reset()
    yield


@pytest.fixture(autouse=True)
def mock_cache_backend():
    """Mock the cache backend to avoid connection issues during tests."""
    with patch("strict.cache.decorators.get_cache") as mock_get_cache:
        mock_instance = mock_get_cache.return_value
        # Use a simple dict-based storage for the mock
        storage = {}

        async def mock_get(key):
            return storage.get(key)

        async def mock_set(key, value, ttl=None):
            storage[key] = value

        mock_instance.get = AsyncMock(side_effect=mock_get)
        mock_instance.set = AsyncMock(side_effect=mock_set)
        yield mock_instance


class TestCacheDecorators:
    """Test cache decorators."""

    @pytest.mark.asyncio
    async def test_cached_decorator_async(self) -> None:
        """Test cached decorator with async function."""

        call_count = 0

        @cached(ttl=60, key_prefix="test")
        async def expensive_function(x: int, y: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return x + y

        # First call - should execute function
        result1 = await expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1

        # Second call with same args - should use cache
        result2 = await expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment

        # Different args - should execute function
        result3 = await expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_cached_decorator_skip_args(self) -> None:
        """Test cached decorator with skip_args parameter."""

        call_count = 0

        @cached(ttl=60, skip_args=("request_id",))
        async def function_with_request_id(x: int, request_id: str) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # These calls should hit the cache despite different request_id
        result1 = await function_with_request_id(5, request_id="req-1")
        result2 = await function_with_request_id(5, request_id="req-2")

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Only called once

    @pytest.mark.asyncio
    async def test_cache_result_decorator(self) -> None:
        """Test cache_result decorator."""

        call_count = 0

        @cache_result(ttl=60)
        async def get_config() -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"setting": "value"}

        # First call
        result1 = await get_config()
        assert result1 == {"setting": "value"}
        assert call_count == 1

        # Second call - should use cache
        result2 = await get_config()
        assert result2 == {"setting": "value"}
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cached_error_handling(self) -> None:
        """Test that cached decorator handles errors gracefully."""

        @cached(ttl=60)
        async def failing_function() -> str:
            raise ValueError("Intentional error")

        # Should fall back to function call on cache error
        with pytest.raises(ValueError, match="Intentional error"):
            await failing_function()


class TestCacheStats:
    """Test cache statistics tracking."""

    def test_cache_stats_initialization(self) -> None:
        """Test that cache stats initialize correctly."""
        assert cache_stats.hits == 0
        assert cache_stats.misses == 0
        assert cache_stats.errors == 0
        assert cache_stats.hit_rate == 0.0

    def test_cache_stats_hit_rate(self) -> None:
        """Test hit rate calculation."""
        cache_stats.record_hit()
        cache_stats.record_hit()
        cache_stats.record_miss()

        assert cache_stats.hit_rate == 2 / 3

    def test_cache_stats_to_dict(self) -> None:
        """Test converting stats to dictionary."""
        cache_stats.record_hit()
        cache_stats.record_miss()
        cache_stats.record_error()

        stats_dict = cache_stats.to_dict()
        assert stats_dict["hits"] == 1
        assert stats_dict["misses"] == 1
        assert stats_dict["errors"] == 1
        assert "hit_rate" in stats_dict


class TestCacheBackendIntegration:
    """Test integration with CacheBackend."""

    @pytest.mark.asyncio
    async def test_cache_key_generation(self) -> None:
        """Test that cache keys are generated correctly."""

        @cached(ttl=60)
        async def test_func(a: int, b: str) -> str:
            return f"{a}-{b}"

        # Same arguments should produce same cache behavior
        result1 = await test_func(1, "hello")
        result2 = await test_func(1, "hello")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_cache_with_different_types(self) -> None:
        """Test caching with different argument types."""

        @cached(ttl=60)
        async def complex_function(
            num: int,
            text: str,
            flag: bool,
            items: list[int],
        ) -> str:
            return f"{num}-{text}-{flag}-{len(items)}"

        result = await complex_function(42, "test", True, [1, 2, 3])
        assert result == "42-test-True-3"

    @pytest.mark.asyncio
    async def test_cache_invalidation_by_time(self) -> None:
        """Test that cache respects TTL (basic check)."""
        # Note: This test doesn't actually wait for TTL to expire
        # It just verifies the mechanism is in place

        call_count = 0

        @cached(ttl=1)  # 1 second TTL
        async def short_lived_cache() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        await short_lived_cache()
        await short_lived_cache()  # Should use cache
        assert call_count == 1
