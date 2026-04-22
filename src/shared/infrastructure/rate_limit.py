# app/repositories/rate_limit_repository.py
import time
import uuid

from src.shared.infrastructure.redis_base import BaseRedisRepository
from src.shared.schemas.rate_limit import RateLimitResponse


class RateLimitRepository(BaseRedisRepository):
    KEY_PREFIX = "rate_limit"

    def _make_key(self, identifier: str) -> str:
        return f"{self.KEY_PREFIX}:{identifier}"

    async def check(
        self,
        identifier: str,
        limit: int = 60,
        window: int = 60,
    ) -> RateLimitResponse:

        key = self._make_key(identifier)
        now = time.time()
        window_start = now - window

        async with self.redis.pipeline() as pipe:
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.expire(key, window)
            results = await pipe.execute()

        current_count: int = results[1]

        if current_count >= limit:
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                _, oldest_score = oldest[0]
                retry_after = int(oldest_score + window - now) + 1
            else:
                retry_after = window

            return RateLimitResponse(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=int(now) + retry_after,
                retry_after=retry_after,
            )

        member = f"{now:.6f}:{uuid.uuid4().hex[:8]}"
        await self.redis.zadd(key, {member: now})

        return RateLimitResponse(
            allowed=True,
            limit=limit,
            remaining=limit - current_count - 1,
            reset_at=int(now + window),
            retry_after=0,
        )

    async def reset(self, identifier: str) -> None:
        await self.delete(self._make_key(identifier))