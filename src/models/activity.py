from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.social import Bookmark, Comment, Like
    from src.models.user import User


class Weekday(StrEnum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


class MuscleGroup(Base):
    __tablename__ = "muscle_group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    primary_exercises: Mapped[list["Exercise"]] = relationship(back_populates="primary_muscle_group")
    secondary_exercise_links: Mapped[list["ExerciseMuscleGroup"]] = relationship(back_populates="muscle_group", cascade="all, delete-orphan")


class ExerciseMuscleGroup(Base):
    __tablename__ = "exercise_muscle_group"
    __table_args__ = (UniqueConstraint("exercise_id", "muscle_group_id"),)

    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True)
    muscle_group_id: Mapped[int] = mapped_column(ForeignKey("muscle_group.id", ondelete="RESTRICT"), primary_key=True)

    exercise: Mapped["Exercise"] = relationship(back_populates="secondary_muscle_group_links")
    muscle_group: Mapped["MuscleGroup"] = relationship(back_populates="secondary_exercise_links")


class Exercise(Base):
    __tablename__ = "exercise"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_muscle_group_id: Mapped[int | None] = mapped_column(ForeignKey("muscle_group.id", ondelete="RESTRICT"))

    primary_muscle_group: Mapped["MuscleGroup | None"] = relationship(back_populates="primary_exercises")
    secondary_muscle_group_links: Mapped[list["ExerciseMuscleGroup"]] = relationship(back_populates="exercise", cascade="all, delete-orphan")
    exercise_sessions: Mapped[list["ExerciseSession"]] = relationship(back_populates="exercise")
    plan_training_exercises: Mapped[list["PlanTrainingExercise"]] = relationship(back_populates="exercise")
    personal_records: Mapped[list["PersonalRecord"]] = relationship(back_populates="exercise")


class WorkoutPlan(Base, TimestampMixin):
    __tablename__ = "workout_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    author: Mapped["User"] = relationship(back_populates="workout_plans")
    comments: Mapped[list["Comment"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    likes: Mapped[list["Like"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    bookmarks: Mapped[list["Bookmark"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    trainings: Mapped[list["PlanTraining"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class PlanTraining(Base):
    __tablename__ = "plan_training"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plan.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    weekday: Mapped[Weekday | None] = mapped_column(SQLAlchemyEnum(Weekday))
    order_num: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="trainings")
    exercises: Mapped[list["PlanTrainingExercise"]] = relationship(back_populates="plan_training", cascade="all, delete-orphan")
    sessions: Mapped[list["WorkoutSession"]] = relationship(back_populates="plan_training")


class PlanTrainingExercise(Base):
    __tablename__ = "plan_training_exercise"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_training_id: Mapped[int] = mapped_column(ForeignKey("plan_training.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id", ondelete="RESTRICT"), nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)
    target_sets: Mapped[int] = mapped_column(Integer, nullable=False)
    target_reps: Mapped[int] = mapped_column(Integer, nullable=False)
    target_weight_pct: Mapped[float | None] = mapped_column(Float)  # % of user's PR; NULL = bodyweight / no PR

    plan_training: Mapped["PlanTraining"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship(back_populates="plan_training_exercises")


class PersonalRecord(Base):
    __tablename__ = "personal_record"
    __table_args__ = (UniqueConstraint("user_id", "exercise_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id", ondelete="RESTRICT"), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="personal_records")
    exercise: Mapped["Exercise"] = relationship(back_populates="personal_records")


class WorkoutSession(Base):
    __tablename__ = "workout_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    plan_training_id: Mapped[int | None] = mapped_column(ForeignKey("plan_training.id", ondelete="SET NULL"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="workout_sessions")
    plan_training: Mapped["PlanTraining | None"] = relationship(back_populates="sessions")
    exercise_sessions: Mapped[list["ExerciseSession"]] = relationship(back_populates="workout_session", cascade="all, delete-orphan")


class ExerciseSession(Base):
    __tablename__ = "exercise_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_session_id: Mapped[int] = mapped_column(ForeignKey("workout_session.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id", ondelete="RESTRICT"), nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)
    is_from_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

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
