from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics_context.audit.domain.interfaces import IAuditEntryRepository
from src.analytics_context.audit.domain.models import AuditChannel, AuditEntry
from src.analytics_context.audit.infrastructure.orm import AuditEntryORM


class AuditEntryRepository(IAuditEntryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: AuditEntry) -> None:
        self._session.add(
            AuditEntryORM(
                id=entry.id,
                channel=str(entry.channel),
                event_type=entry.event_type,
                user_id=entry.user_id,
                occurred_at=entry.occurred_at,
                payload=entry.payload,
            )
        )

    async def list(
        self,
        *,
        user_id: int | None = None,
        channel: AuditChannel | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        stmt = select(AuditEntryORM).order_by(AuditEntryORM.occurred_at.desc()).limit(limit)
        if user_id is not None:
            stmt = stmt.where(AuditEntryORM.user_id == user_id)
        if channel is not None:
            stmt = stmt.where(AuditEntryORM.channel == str(channel))
        if since is not None:
            stmt = stmt.where(AuditEntryORM.occurred_at >= since)

        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def get(self, entry_id: UUID) -> AuditEntry | None:
        row = await self._session.get(AuditEntryORM, entry_id)
        return _to_domain(row) if row else None


def _to_domain(row: AuditEntryORM) -> AuditEntry:
    return AuditEntry(
        id=row.id,
        channel=AuditChannel(row.channel),
        event_type=row.event_type,
        user_id=row.user_id,
        occurred_at=row.occurred_at,
        payload=row.payload or {},
    )
