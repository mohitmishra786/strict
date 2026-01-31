import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from strict.storage.cache import CacheManager
from strict.storage.object_store import ObjectStore


@pytest.mark.asyncio
async def test_cache_get_set():
    with patch("strict.storage.cache.redis.from_url") as mock_redis_cls:
        mock_redis = AsyncMock()
        mock_redis_cls.return_value = mock_redis

        cache = CacheManager()

        # Test Set
        await cache.set("key", "value")
        mock_redis.set.assert_called_with("key", '"value"', ex=3600)

        # Test Get
        mock_redis.get.return_value = '"value"'
        val = await cache.get("key")
        assert val == "value"


@pytest.mark.asyncio
async def test_s3_upload():
    with patch("aioboto3.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_client = AsyncMock()
        mock_session.client.return_value.__aenter__.return_value = mock_client

        store = ObjectStore()
        await store.upload("test.txt", b"data")

        mock_client.put_object.assert_called()
