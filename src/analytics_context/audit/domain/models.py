from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class AuditChannel(StrEnum):
    AUTH = "auth"
    ACTIVITY = "activity"
    NUTRITION = "nutrition"
    GAMIFICATION = "gamification"
    USER = "user"


@dataclass(frozen=True)
class AuditEntry:
    channel: AuditChannel
    event_type: str
    occurred_at: datetime
    user_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
