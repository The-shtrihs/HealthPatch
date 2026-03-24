import json
from typing import Any

import redis.asyncio as aioredis


class BaseRedisRepository:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:

        result = await self.redis.set(key, value, ex=ttl, nx=nx, xx=xx)
        return result is not None

    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)

    async def delete(self, *keys: str) -> int:
        if not keys:
            return 0
        return await self.redis.delete(*keys)

    async def exists(self, key: str) -> bool:
        return bool(await self.redis.exists(key))

    async def ttl(self, key: str) -> int:
        return await self.redis.ttl(key)

    async def expire(self, key: str, seconds: int) -> bool:
        return bool(await self.redis.expire(key, seconds))

    async def persist(self, key: str) -> bool:
        return bool(await self.redis.persist(key))

    async def getdel(self, key: str) -> str | None:
        return await self.redis.getdel(key)

    async def getex(self, key: str, ex: int | None = None) -> str | None:
        return await self.redis.getex(key, ex=ex)

    async def incr(self, key: str, amount: int = 1) -> int:
        return await self.redis.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        return await self.redis.decrby(key, amount)

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        serialized = json.dumps(value, default=str, ensure_ascii=False)
        await self.redis.set(key, serialized, ex=ttl)

    async def get_json(self, key: str) -> Any | None:
        raw = await self.redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def getdel_json(self, key: str) -> Any | None:
        raw = await self.redis.getdel(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def mset(self, mapping: dict[str, str]) -> None:
        await self.redis.mset(mapping)

    async def mget(self, *keys: str) -> list[str | None]:
        return await self.redis.mget(*keys)

    async def scan_keys(
        self,
        pattern: str,
        count: int = 100,
    ) -> list[str]:
        keys = []
        async for key in self.redis.scan_iter(match=pattern, count=count):
            keys.append(key)
        return keys

    async def delete_by_pattern(self, pattern: str) -> int:
        deleted = 0
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)
            deleted += 1
        return deleted

    async def ping(self) -> bool:
        try:
            result = await self.redis.ping()
            return result is True
        except Exception:
            return False
