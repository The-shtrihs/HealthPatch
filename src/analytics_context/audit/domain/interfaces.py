from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.analytics_context.audit.domain.models import AuditChannel, AuditEntry


class IAuditEntryRepository(ABC):
    @abstractmethod
    async def add(self, entry: AuditEntry) -> None: ...

    @abstractmethod
    async def list(
        self,
        *,
        user_id: int | None = None,
        channel: AuditChannel | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]: ...

    @abstractmethod
    async def get(self, entry_id: UUID) -> AuditEntry | None: ...
