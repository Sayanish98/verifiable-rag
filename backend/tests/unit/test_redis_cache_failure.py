import pytest

from app.integrations.redis_client import RedisCache


class BrokenRedis:
    async def get(self, key):
        raise ConnectionError("redis down")

    async def set(self, key, value, ex=None):
        raise ConnectionError("redis down")


@pytest.mark.asyncio
async def test_redis_cache_degrades_when_unavailable():
    cache = RedisCache(BrokenRedis(), ttl_seconds=60)

    assert await cache.get_json("cache-key") is None
    await cache.set_json("cache-key", {"ok": True})

