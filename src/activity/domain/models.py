from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from src.activity.domain.errors import (
    InvalidPlanTitleError,
    InvalidRepsError,
    InvalidSetNumberError,
    InvalidTimeRangeError,
    InvalidWeightError,
    SessionAlreadyEndedError,
)


class Weekday(StrEnum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


@dataclass(frozen=True)
class WeightKg:
    """Value Object: non-negative weight in kilograms."""

    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidWeightError()

    def is_greater_than(self, other: "WeightKg") -> bool:
        return self.value > other.value


@dataclass(frozen=True)
class RepCount:
    """Value Object: positive number of repetitions."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise InvalidRepsError()


@dataclass(frozen=True)
class SetNumber:
    """Value Object: positive ordinal for sets within an exercise session."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise InvalidSetNumberError()


@dataclass(frozen=True)
class TimeRange:
    """Value Object: started_at .. ended_at, where ended_at may be None (open)."""

    started_at: datetime
    ended_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise InvalidTimeRangeError()

    @property
    def is_closed(self) -> bool:
        return self.ended_at is not None

    def duration_minutes(self) -> float | None:
        if self.ended_at is None:
            return None
        return round((self.ended_at - self.started_at).total_seconds() / 60, 2)


@dataclass
class MuscleGroupDomain:
    id: int | None
    name: str


@dataclass
class ExerciseDomain:
    id: int | None
    name: str
    primary_muscle_group: MuscleGroupDomain | None
    secondary_muscle_groups: list[MuscleGroupDomain] = field(default_factory=list)


@dataclass
class PlanTrainingExerciseDomain:
    id: int | None
    plan_training_id: int | None
    exercise_id: int
    exercise_name: str | None
    order_num: int
    target_sets: int
    target_reps: int
    target_weight_pct: float | None


@dataclass
class PlanTrainingDomain:
    id: int | None
    plan_id: int | None
    name: str
    weekday: Weekday | None
    order_num: int
    exercises: list[PlanTrainingExerciseDomain] = field(default_factory=list)


@dataclass
class WorkoutPlanDomain:
    id: int | None
    author_id: int
    title: str
    description: str | None
    is_public: bool
    trainings: list[PlanTrainingDomain] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise InvalidPlanTitleError()

    def update_details(
        self,
        title: str | None = None,
        description: str | None = None,
        is_public: bool | None = None,
    ) -> None:
        if title is not None:
            if not title.strip():
                raise InvalidPlanTitleError()
            self.title = title
        if description is not None:
            self.description = description
        if is_public is not None:
            self.is_public = is_public

    def is_visible_to(self, user_id: int) -> bool:
        return self.is_public or self.author_id == user_id

    def is_owned_by(self, user_id: int) -> bool:
        return self.author_id == user_id


@dataclass
class WorkoutSetDomain:
    id: int | None
    exercise_session_id: int
    set_number: SetNumber
    reps: RepCount
    weight: WeightKg


@dataclass
class ExerciseSessionDomain:
    id: int | None
    workout_session_id: int
    exercise_id: int
    exercise_name: str | None
    order_num: int
    is_from_template: bool
    sets: list[WorkoutSetDomain] = field(default_factory=list)


@dataclass
class WorkoutSessionDomain:
    id: int | None
    user_id: int
    plan_training_id: int | None
    time_range: TimeRange
    exercise_sessions: list[ExerciseSessionDomain] = field(default_factory=list)

    @property
    def started_at(self) -> datetime:
        return self.time_range.started_at

    @property
    def ended_at(self) -> datetime | None:
        return self.time_range.ended_at

    @property
    def is_ended(self) -> bool:
        return self.time_range.is_closed

    def duration_minutes(self) -> float | None:
        return self.time_range.duration_minutes()

    def is_owned_by(self, user_id: int) -> bool:
        return self.user_id == user_id

    def end(self, at: datetime) -> None:
        if self.is_ended:
            raise SessionAlreadyEndedError()
        self.time_range = TimeRange(started_at=self.time_range.started_at, ended_at=at)

    def ensure_can_be_modified(self, message: str | None = None) -> None:
        if self.is_ended:
            raise SessionAlreadyEndedError(message or "Workout session has already ended")


@dataclass
class PersonalRecordDomain:
    id: int | None
    user_id: int
    exercise_id: int
    exercise_name: str | None
    weight: WeightKg
    recorded_at: datetime

    def is_owned_by(self, user_id: int) -> bool:
        return self.user_id == user_id

    def update(self, new_weight: WeightKg, at: datetime) -> None:
        self.weight = new_weight
        self.recorded_at = at
