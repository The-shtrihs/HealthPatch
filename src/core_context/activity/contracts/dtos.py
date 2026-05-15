from pydantic import BaseModel, ConfigDict


class ExerciseDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    exercise_id: int
    name: str
    muscle_group: str | None = None


class WorkoutSummaryDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    workout_id: int
    user_id: int
    duration_seconds: int
    total_volume_kg: float | None = None
    exercise_count: int = 0
