# app/repositories/cache_repository.py
import hashlib
from collections.abc import Callable
from typing import Any

from src.repositories.redis_base import BaseRedisRepository


class CacheRepository(BaseRedisRepository):
    KEY_PREFIX = "cache"

    def make_key(self, namespace: str, *parts: Any) -> str:
        raw_key = f"{self.KEY_PREFIX}:{namespace}:" + ":".join(str(p) for p in parts)

        if len(raw_key) > 200:
            hash_part = hashlib.sha1(raw_key.encode()).hexdigest()
            return f"{self.KEY_PREFIX}:{namespace}:{hash_part}"

        return raw_key

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = 300,
    ) -> Any:

        cached = await self.get_json(key)
        if cached is not None:
            return cached

        result = await factory()

        if result is not None:
            await self.set_json(key, result, ttl=ttl)

        return result

    async def invalidate(self, *keys: str) -> int:
        return await self.delete(*keys)

    async def invalidate_namespace(self, namespace: str) -> int:
        pattern = f"{self.KEY_PREFIX}:{namespace}:*"
        return await self.delete_by_pattern(pattern)

    def user_profile_key(self, user_id: int) -> str:
        return self.make_key("user", user_id, "profile")

    def user_stats_key(self, user_id: int) -> str:
        return self.make_key("user", user_id, "stats")

    def post_key(self, post_id: int) -> str:
        return self.make_key("post", post_id)

    def feed_key(self, user_id: int, page: int) -> str:
        return self.make_key("feed", user_id, f"page{page}")
