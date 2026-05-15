from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.analytics_context.audit.domain.models import AuditChannel, AuditEntry


class AuditEntryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    channel: AuditChannel
    event_type: str
    user_id: int | None
    occurred_at: datetime
    payload: dict[str, Any]

    @classmethod
    def from_domain(cls, entry: AuditEntry) -> "AuditEntryResponse":
        return cls(
            id=entry.id,
            channel=entry.channel,
            event_type=entry.event_type,
            user_id=entry.user_id,
            occurred_at=entry.occurred_at,
            payload=entry.payload,
        )
