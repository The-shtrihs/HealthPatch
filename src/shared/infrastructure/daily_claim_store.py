from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta, timezone

import src.core.redis as redis_module


class DailyClaimStore(ABC):
    @abstractmethod
    async def try_claim(self, user_id: int, target_date) -> bool: ...


class RedisDailyClaimStore(DailyClaimStore):
    async def try_claim(self, user_id: int, target_date) -> bool:
        redis = redis_module.get_redis()

        key_date = getattr(target_date, "isoformat", lambda: str(target_date))()
        key = f"daily_norm:{user_id}:{key_date}"

        try:
            if hasattr(target_date, "date"):
                date_part = target_date.date() if isinstance(target_date, datetime) else target_date
            else:
                date_part = target_date

            next_midnight = datetime.combine(date_part, time.min, tzinfo=timezone.utc) + timedelta(days=1)
            now = datetime.now(timezone.utc)
            expiry_seconds = int((next_midnight - now).total_seconds())
            if expiry_seconds <= 0:
                expiry_seconds = 60 * 60 * 24
        except Exception:
            expiry_seconds = 60 * 60 * 24

        was_set = await redis.set(key, "1", nx=True, ex=expiry_seconds)
        return bool(was_set)