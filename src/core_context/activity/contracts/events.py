from src.shared.contracts.integration_event import IntegrationEvent


class WorkoutCompleted(IntegrationEvent):
    user_id: int
    duration_minutes: float | None = None
    total_volume_kg: float = 0.0


class PersonalRecordBeaten(IntegrationEvent):
    user_id: int
    exercise_id: int
    new_weight_kg: float
    previous_weight_kg: float | None = None


class WorkoutPlanCreated(IntegrationEvent):
    plan_id: int
    author_user_id: int
    title: str
    is_public: bool


class WorkoutPlanPublished(IntegrationEvent):
    plan_id: int
    author_user_id: int
    title: str
