from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import Base, TimestampMixin

from src.models.social import  Comment, Like, Bookmark
from src.models.activity import WorkoutSession, DeviceSyncMetric, WorkoutPlan
from src.models.nutrition import DailyDiary


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


    workout_plans: Mapped[list["WorkoutPlan"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[list["Like"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bookmarks: Mapped[list["Bookmark"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    workout_sessions: Mapped[list["WorkoutSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    device_metrics: Mapped[list["DeviceSyncMetric"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    daily_diaries: Mapped[list["DailyDiary"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    height: Mapped[Optional[float]] = mapped_column(Float)
    fitness_goal: Mapped[Optional[str]] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="profile")