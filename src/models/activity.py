from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import Base, TimestampMixin


from src.models.user import User
from src.models.social import Comment, Like, Bookmark


class WorkoutPlan(Base, TimestampMixin):
    __tablename__ = "workout_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    author: Mapped["User"] = relationship(back_populates="workout_plans")
    comments: Mapped[list["Comment"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    likes: Mapped[list["Like"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    bookmarks: Mapped[list["Bookmark"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    sessions: Mapped[list["WorkoutSession"]] = relationship(back_populates="plan")


class Exercise(Base):
    __tablename__ = "exercise"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    muscle_group: Mapped[Optional[str]] = mapped_column(String(100))

    exercise_sessions: Mapped[list["ExerciseSession"]] = relationship(back_populates="exercise")


class WorkoutSession(Base):
    __tablename__ = "workout_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workout_plan.id", ondelete="SET NULL"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="workout_sessions")
    plan: Mapped[Optional["WorkoutPlan"]] = relationship(back_populates="sessions")
    exercise_sessions: Mapped[list["ExerciseSession"]] = relationship(back_populates="workout_session", cascade="all, delete-orphan")


class ExerciseSession(Base):
    __tablename__ = "exercise_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_session_id: Mapped[int] = mapped_column(ForeignKey("workout_session.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id", ondelete="RESTRICT"), nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)

    workout_session: Mapped["WorkoutSession"] = relationship(back_populates="exercise_sessions")
    exercise: Mapped["Exercise"] = relationship(back_populates="exercise_sessions")
    sets: Mapped[list["WorkoutSet"]] = relationship(back_populates="exercise_session", cascade="all, delete-orphan")


class WorkoutSet(Base):
    __tablename__ = "workout_set"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_session_id: Mapped[int] = mapped_column(ForeignKey("exercise_session.id", ondelete="CASCADE"), nullable=False)
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)

    exercise_session: Mapped["ExerciseSession"] = relationship(back_populates="sets")
