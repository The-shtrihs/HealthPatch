from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics_context.audit.domain.models import AuditChannel, AuditEntry
from src.analytics_context.audit.infrastructure.repository import AuditEntryRepository


class AuditQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AuditEntryRepository(session)

    async def list(
        self,
        *,
        user_id: int | None = None,
        channel: AuditChannel | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        return await self._repo.list(user_id=user_id, channel=channel, since=since, limit=limit)
