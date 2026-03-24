import secrets
from datetime import UTC, datetime

from src.core.config import get_settings
from src.repositories.redis_base import BaseRedisRepository
from src.schemas.oauth import OAuthStateData

settings = get_settings()

class OAuthStateRepository(BaseRedisRepository):

    KEY_PREFIX = "oauth_state"
    DEFAULT_TTL = settings.oauth_state_expire_seconds   

    def _make_key(self, state: str) -> str:
        return f"{self.KEY_PREFIX}:{state}"

    def _generate_state(self) -> str:
        return secrets.token_urlsafe(32)

    async def create(
        self,
        provider: str,
        redirect_after: str = "/",
        ip_address: str | None = None,
        ttl: int = DEFAULT_TTL,
    ) -> str:
        state = self._generate_state()
        
        data = OAuthStateData(
            provider=provider,
            redirect_after=redirect_after,
            created_at=datetime.now(UTC).isoformat(),
            ip_address=ip_address,
        )
        
        await self.set_json(self._make_key(state), data.model_dump(), ttl=ttl)
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