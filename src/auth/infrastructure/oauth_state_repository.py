import secrets
from datetime import UTC, datetime

import redis.asyncio as aioredis

from src.auth.domain.interfaces import IOAuthStateRepository
from src.auth.domain.models import OAuthStateData
from src.core.config import get_settings
from src.core.constants import OAUTH_STATE_TOKEN_BYTES
from src.shared.infrastructure.redis_base import BaseRedisRepository

_settings = get_settings()


class RedisOAuthStateRepository(BaseRedisRepository, IOAuthStateRepository):
    KEY_PREFIX = "oauth_state"
    DEFAULT_TTL: int = _settings.oauth_state_expire_seconds

    def __init__(self, redis: aioredis.Redis) -> None:
        super().__init__(redis)

    def _make_key(self, state: str) -> str:
        return f"{self.KEY_PREFIX}:{state}"

    async def create(
        self,
        provider: str,
        redirect_after: str = "/",
        ip_address: str | None = None,
    ) -> str:
        state = secrets.token_urlsafe(OAUTH_STATE_TOKEN_BYTES)
        data = OAuthStateData(
            provider=provider,
            redirect_after=redirect_after,
            created_at=datetime.now(UTC).isoformat(),
            ip_address=ip_address,
        )
        await self.set_json(
            self._make_key(state),
            {
                "provider": data.provider,
                "redirect_after": data.redirect_after,
                "created_at": data.created_at,
                "ip_address": data.ip_address,
            },
            ttl=self.DEFAULT_TTL,
        )
        return state

    async def validate_and_consume(self, state: str) -> OAuthStateData | None:
        raw = await self.getdel_json(self._make_key(state))
        if raw is None:
            return None
        return OAuthStateData(**raw)

    async def peek(self, state: str) -> OAuthStateData | None:
        raw = await self.get_json(self._make_key(state))
        if raw is None:
            return None
        return OAuthStateData(**raw)

    async def revoke(self, state: str) -> bool:
        deleted = await self.delete(self._make_key(state))
        return deleted > 0

    async def get_remaining_ttl(self, state: str) -> int:
        return await self.ttl(self._make_key(state))