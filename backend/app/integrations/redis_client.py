import json
from typing import Any

import redis.asyncio as redis

from app.core.config import Settings
from app.core.logging import log_event


class RedisCache:
    def __init__(self, client: redis.Redis | None, ttl_seconds: int):
        self.client = client
        self.ttl_seconds = ttl_seconds

    async def get_json(self, key: str) -> dict[str, Any] | None:
        if self.client is None:
            return None
        try:
            raw = await self.client.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:
            log_event("redis_cache_get_failed", key=key, error=str(exc))
            return None

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
        if self.client is None:
            return
        try:
            await self.client.set(key, json.dumps(value, default=str), ex=ttl_seconds or self.ttl_seconds)
        except Exception as exc:
            log_event("redis_cache_set_failed", key=key, error=str(exc))


async def create_redis_cache(settings: Settings) -> RedisCache:
    if not settings.redis_url:
        return RedisCache(None, settings.query_cache_ttl_seconds)
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        return RedisCache(client, settings.query_cache_ttl_seconds)
    except Exception as exc:
        log_event("redis_unavailable", error=str(exc))
        return RedisCache(None, settings.query_cache_ttl_seconds)

