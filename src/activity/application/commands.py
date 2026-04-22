from dataclasses import dataclass, field

from src.activity.domain.models import Weekday


@dataclass
class CreateMuscleGroupCommand:
    name: str


@dataclass
class CreateExerciseCommand:
    name: str
    primary_muscle_group_id: int | None
    secondary_muscle_group_ids: list[int]


@dataclass
class PlanTrainingExerciseInput:
    exercise_id: int
    order_num: int
    target_sets: int
    target_reps: int
    target_weight_pct: float | None


@dataclass
class PlanTrainingInput:
    name: str
    order_num: int
    weekday: Weekday | None
    exercises: list[PlanTrainingExerciseInput] = field(default_factory=list)


@dataclass
class CreateWorkoutPlanCommand:
    author_id: int
    title: str
    description: str | None
    is_public: bool
    trainings: list[PlanTrainingInput] = field(default_factory=list)


@dataclass
class UpdateWorkoutPlanCommand:
    plan_id: int
    user_id: int
    title: str | None
    description: str | None
    is_public: bool | None


@dataclass
class DeleteWorkoutPlanCommand:
    plan_id: int
    user_id: int


@dataclass
class AddTrainingCommand:
    plan_id: int
    user_id: int
    name: str
    weekday: Weekday | None
    order_num: int


@dataclass
class DeleteTrainingCommand:
    plan_id: int
    training_id: int
    user_id: int


@dataclass
class AddExerciseToTrainingCommand:
    plan_id: int
    training_id: int
    user_id: int
    exercise_id: int
    order_num: int
    target_sets: int
    target_reps: int
    target_weight_pct: float | None


@dataclass
class DeleteTrainingExerciseCommand:
    plan_id: int
    training_id: int
    pte_id: int
    user_id: int


@dataclass
class StartSessionCommand:
    user_id: int
    plan_training_id: int | None


@dataclass
class EndSessionCommand:
    session_id: int
    user_id: int


@dataclass
class AddExerciseToSessionCommand:
    session_id: int
    user_id: int
    exercise_id: int
    order_num: int


@dataclass
class LogSetCommand:
    session_id: int
    exercise_session_id: int
    user_id: int
    set_number: int
    reps: int
    weight: float


@dataclass
class UpsertPersonalRecordCommand:
    user_id: int
    exercise_id: int
    weight: float


@dataclass
class DeletePersonalRecordCommand:
    pr_id: int
    user_id: int
