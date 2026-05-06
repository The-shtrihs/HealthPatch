from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorkoutSessionStarted:
    session_id: int
    user_id: int
    plan_training_id: int | None
    started_at: datetime


@dataclass(frozen=True)
class WorkoutSessionEnded:
    session_id: int
    user_id: int
    ended_at: datetime
    duration_minutes: float | None


@dataclass(frozen=True)
class ExerciseSessionAdded:
    exercise_session_id: int
    session_id: int
    user_id: int
    exercise_id: int
    is_from_template: bool


@dataclass(frozen=True)
class SetLogged:
    set_id: int
    session_id: int
    exercise_session_id: int
    exercise_id: int
    user_id: int
    set_number: int
    reps: int
    weight_kg: float


@dataclass(frozen=True)
class PersonalRecordBeaten:
    user_id: int
    exercise_id: int
    new_weight_kg: float
    previous_weight_kg: float | None  # None when it's the first record for this exercise
    recorded_at: datetime


@dataclass(frozen=True)
class PersonalRecordUpserted:
    pr_id: int
    user_id: int
    exercise_id: int
    weight_kg: float
    recorded_at: datetime


@dataclass(frozen=True)
class WorkoutPlanCreated:
    plan_id: int
    author_id: int
    title: str
    is_public: bool


@dataclass(frozen=True)
class WorkoutPlanMadePublic:
    plan_id: int
    author_id: int
    title: str


@dataclass(frozen=True)
class WorkoutPlanDeleted:
    plan_id: int
    author_id: int


ActivityEvent = (
    WorkoutSessionStarted
    | WorkoutSessionEnded
    | ExerciseSessionAdded
    | SetLogged
    | PersonalRecordBeaten
    | PersonalRecordUpserted
    | WorkoutPlanCreated
    | WorkoutPlanMadePublic
    | WorkoutPlanDeleted
)
