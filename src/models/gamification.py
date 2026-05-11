from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User


class GamificationProfile(Base, TimestampMixin):
    __tablename__ = "gamification_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[User] = relationship(back_populates="gamification_profile")
