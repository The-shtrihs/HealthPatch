from datetime import datetime

from src.analytics_context.audit.domain.interfaces import IAuditEntryRepository
from src.analytics_context.audit.domain.models import AuditChannel, AuditEntry


class AuditQueryService:
    def __init__(self, repo: IAuditEntryRepository) -> None:
        self._repo = repo

    async def list(
        self,
        *,
        user_id: int | None = None,
        channel: AuditChannel | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        return await self._repo.list(user_id=user_id, channel=channel, since=since, limit=limit)
