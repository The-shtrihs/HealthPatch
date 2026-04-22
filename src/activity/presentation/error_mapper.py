from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.activity.domain.errors import (
    ActivityDomainError,
    ExerciseNotFoundError,
    ExerciseSessionNotFoundError,
    InvalidPlanTitleError,
    InvalidRepsError,
    InvalidSetNumberError,
    InvalidTimeRangeError,
    InvalidWeightError,
    MuscleGroupNotFoundError,
    NotResourceOwnerError,
    PersonalRecordDowngradeError,
    PersonalRecordNotFoundError,
    PlanTrainingExerciseNotFoundError,
    PlanTrainingNotFoundError,
    PrivatePlanAccessError,
    SessionAlreadyEndedError,
    WorkoutPlanNotFoundError,
    WorkoutSessionNotFoundError,
)

_ERROR_MAP: dict[type[ActivityDomainError], tuple[int, str]] = {
    WorkoutPlanNotFoundError: (404, "WORKOUT_PLAN_NOT_FOUND"),
    PlanTrainingNotFoundError: (404, "PLAN_TRAINING_NOT_FOUND"),
    PlanTrainingExerciseNotFoundError: (404, "PLAN_TRAINING_EXERCISE_NOT_FOUND"),
    ExerciseNotFoundError: (404, "EXERCISE_NOT_FOUND"),
    MuscleGroupNotFoundError: (404, "MUSCLE_GROUP_NOT_FOUND"),
    WorkoutSessionNotFoundError: (404, "WORKOUT_SESSION_NOT_FOUND"),
    ExerciseSessionNotFoundError: (404, "EXERCISE_SESSION_NOT_FOUND"),
    PersonalRecordNotFoundError: (404, "PERSONAL_RECORD_NOT_FOUND"),
    NotResourceOwnerError: (403, "NOT_RESOURCE_OWNER"),
    PrivatePlanAccessError: (403, "PRIVATE_PLAN_ACCESS"),
    SessionAlreadyEndedError: (409, "SESSION_ALREADY_ENDED"),
    PersonalRecordDowngradeError: (400, "PR_DOWNGRADE"),
    InvalidWeightError: (400, "INVALID_WEIGHT"),
    InvalidRepsError: (400, "INVALID_REPS"),
    InvalidSetNumberError: (400, "INVALID_SET_NUMBER"),
    InvalidTimeRangeError: (400, "INVALID_TIME_RANGE"),
    InvalidPlanTitleError: (400, "INVALID_PLAN_TITLE"),
}


def setup_activity_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ActivityDomainError)
    async def handle(request, exc: ActivityDomainError):
        status_code, error_code = _ERROR_MAP.get(type(exc), (500, "DOMAIN_ERROR"))
        return JSONResponse(
            status_code=status_code,
            content={
                "error_code": error_code,
                "message": exc.message,
                "timestamp": datetime.now(UTC).isoformat(),
                "path": str(request.url.path),
            },
        )
