from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.activity import WorkoutPlan
    from src.models.user import User


class Comment(Base, TimestampMixin):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plan.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(back_populates="comments")


class Like(Base, TimestampMixin):
    __tablename__ = "plan_like"
    __table_args__ = (UniqueConstraint("plan_id", "user_id"),)

    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plan.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="likes")
    user: Mapped["User"] = relationship(back_populates="likes")


class Bookmark(Base):
    __tablename__ = "plan_bookmark"
    __table_args__ = (UniqueConstraint("plan_id", "user_id"),)

    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plan.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="bookmarks")
    user: Mapped["User"] = relationship(back_populates="bookmarks")
