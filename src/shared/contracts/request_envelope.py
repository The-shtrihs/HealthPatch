from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class RequestEnvelope[PayloadT](BaseModel):
    model_config = ConfigDict(frozen=True)

    correlation_id: UUID = Field(default_factory=uuid4)
    reply_to: str
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: PayloadT


class ResponseEnvelope[PayloadT](BaseModel):
    model_config = ConfigDict(frozen=True)

    correlation_id: UUID
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: PayloadT | None = None
    error: str | None = None

    @classmethod
    def ok(cls, correlation_id: UUID, payload: Any) -> "ResponseEnvelope":
        return cls(correlation_id=correlation_id, payload=payload)

    @classmethod
    def fail(cls, correlation_id: UUID, error: str) -> "ResponseEnvelope":
        return cls(correlation_id=correlation_id, error=error)
