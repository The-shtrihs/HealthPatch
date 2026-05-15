from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base import Base


class ActivityHistoryEntry(Base):
    __tablename__ = "analytics_activity_history"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_volume_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
