from dataclasses import dataclass, field
from datetime import datetime

from src.activity.domain.models import Weekday


@dataclass
class PageReadModel[T]:
    items: list[T]
    total: int
    page: int
    size: int


@dataclass
class MuscleGroupReadModel:
    id: int
    name: str


@dataclass
class ExerciseReadModel:
    id: int
    name: str
    primary_muscle_group: MuscleGroupReadModel | None
    secondary_muscle_groups: list[MuscleGroupReadModel] = field(default_factory=list)


@dataclass
class PlanTrainingExerciseReadModel:
    id: int
    exercise_id: int
    exercise_name: str
    order_num: int
    target_sets: int
    target_reps: int
    target_weight_pct: float | None


@dataclass
class PlanTrainingReadModel:
    id: int
    plan_id: int
    name: str
    weekday: Weekday | None
    order_num: int
    exercises: list[PlanTrainingExerciseReadModel] = field(default_factory=list)


@dataclass
class WorkoutPlanSummaryReadModel:
    id: int
    author_id: int
    title: str
    description: str | None
    is_public: bool


@dataclass
class WorkoutPlanDetailReadModel:
    id: int
    author_id: int
    title: str
    description: str | None
    is_public: bool
    trainings: list[PlanTrainingReadModel] = field(default_factory=list)


@dataclass
class WorkoutSetReadModel:
    id: int
    set_number: int
    reps: int
    weight: float


@dataclass
class ExerciseSessionReadModel:
    id: int
    exercise_id: int
    exercise_name: str
    order_num: int
    is_from_template: bool
    sets: list[WorkoutSetReadModel] = field(default_factory=list)


@dataclass
class WorkoutSessionSummaryReadModel:
    id: int
    user_id: int
    plan_training_id: int | None
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: float | None


@dataclass
class WorkoutSessionDetailReadModel:
    id: int
    user_id: int
    plan_training_id: int | None
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: float | None
    exercise_sessions: list[ExerciseSessionReadModel] = field(default_factory=list)


@dataclass
class PersonalRecordReadModel:
    id: int
    user_id: int
    exercise_id: int
    exercise_name: str
    weight: float
    recorded_at: datetime
