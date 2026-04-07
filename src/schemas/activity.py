from pydantic import BaseModel, ConfigDict, Field

from src.models.activity import Weekday


class MuscleGroupResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CreateMuscleGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CreateExerciseRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    primary_muscle_group_id: int | None = Field(default=None, gt=0)
    secondary_muscle_group_ids: list[int] = Field(default_factory=list)


class ExerciseResponse(BaseModel):
    id: int
    name: str
    primary_muscle_group: MuscleGroupResponse | None
    secondary_muscle_groups: list[MuscleGroupResponse]

    model_config = ConfigDict(from_attributes=True)


class ExerciseListResponse(BaseModel):
    items: list[ExerciseResponse]
    total: int
    page: int
    size: int


class TrainingExerciseInput(BaseModel):
    exercise_id: int = Field(gt=0)
    order_num: int = Field(gt=0)
    target_sets: int = Field(gt=0)
    target_reps: int = Field(gt=0)
    target_weight_pct: float | None = Field(default=None, gt=0, le=200)


class TrainingInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    order_num: int = Field(default=0, ge=0)
    weekday: Weekday | None = None
    exercises: list[TrainingExerciseInput] = Field(default_factory=list)


class CreateWorkoutPlanRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_public: bool = False
    trainings: list[TrainingInput] = Field(default_factory=list)


class UpdateWorkoutPlanRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_public: bool | None = None


class WorkoutPlanResponse(BaseModel):
    id: int
    author_id: int
    title: str
    description: str | None
    is_public: bool

    model_config = ConfigDict(from_attributes=True)


class WorkoutPlanListResponse(BaseModel):
    items: list[WorkoutPlanResponse]
    total: int
    page: int
    size: int


class CreatePlanTrainingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    weekday: Weekday | None = None
    order_num: int = Field(default=0, ge=0)


class PlanTrainingExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str
    order_num: int
    target_sets: int
    target_reps: int
    target_weight_pct: float | None

    model_config = ConfigDict(from_attributes=True)


class PlanTrainingResponse(BaseModel):
    id: int
    plan_id: int
    name: str
    weekday: Weekday | None
    order_num: int
    exercises: list[PlanTrainingExerciseResponse]

    model_config = ConfigDict(from_attributes=True)


class PlanDetailResponse(BaseModel):
    id: int
    author_id: int
    title: str
    description: str | None
    is_public: bool
    trainings: list[PlanTrainingResponse]

    model_config = ConfigDict(from_attributes=True)


class AddExerciseToTrainingRequest(BaseModel):
    exercise_id: int = Field(gt=0)
    order_num: int = Field(gt=0)
    target_sets: int = Field(gt=0)
    target_reps: int = Field(gt=0)
    target_weight_pct: float | None = Field(default=None, gt=0, le=200)


class StartSessionRequest(BaseModel):
    plan_training_id: int | None = Field(default=None, gt=0)


class WorkoutSetResponse(BaseModel):
    id: int
    set_number: int
    reps: int
    weight: float

    model_config = ConfigDict(from_attributes=True)


class ExerciseSessionResponse(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str
    order_num: int
    is_from_template: bool
    sets: list[WorkoutSetResponse]

    model_config = ConfigDict(from_attributes=True)


class WorkoutSessionResponse(BaseModel):
    id: int
    user_id: int
    plan_training_id: int | None
    started_at: str
    ended_at: str | None
    duration_minutes: float | None

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(BaseModel):
    id: int
    user_id: int
    plan_training_id: int | None
    started_at: str
    ended_at: str | None
    duration_minutes: float | None
    exercise_sessions: list[ExerciseSessionResponse]

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    items: list[WorkoutSessionResponse]
    total: int
    page: int
    size: int


class AddExerciseToSessionRequest(BaseModel):
    exercise_id: int = Field(gt=0)
    order_num: int = Field(gt=0)


class LogSetRequest(BaseModel):
    set_number: int = Field(gt=0)
    reps: int = Field(gt=0)
    weight: float = Field(ge=0)


class UpsertPersonalRecordRequest(BaseModel):
    exercise_id: int = Field(gt=0)
    weight: float = Field(gt=0)


class PersonalRecordResponse(BaseModel):
    id: int
    user_id: int
    exercise_id: int
    exercise_name: str
    weight: float
    recorded_at: str

    model_config = ConfigDict(from_attributes=True)


class DeletePersonalRecordResponse(BaseModel):
    deleted_pr_id: int
