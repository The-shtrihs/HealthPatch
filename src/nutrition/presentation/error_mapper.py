from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.nutrition.domain.errors import (
    IncompleteNutritionProfileError,
    InvalidMealEntryError,
    MealEntryNotFoundError,
    NutritionDomainError,
    NutritionProfileNotFoundError,
    UnsupportedActivityLevelError,
    UnsupportedFitnessGoalError,
    UnsupportedGenderError,
)

_ERROR_MAP: dict[type[NutritionDomainError], tuple[int, str]] = {
    NutritionProfileNotFoundError: (404, "NOT_FOUND"),
    MealEntryNotFoundError: (404, "NOT_FOUND"),
    IncompleteNutritionProfileError: (400, "BAD_REQUEST"),
    InvalidMealEntryError: (400, "BAD_REQUEST"),
    UnsupportedGenderError: (400, "BAD_REQUEST"),
    UnsupportedFitnessGoalError: (400, "BAD_REQUEST"),
    UnsupportedActivityLevelError: (400, "BAD_REQUEST"),
}


def setup_nutrition_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NutritionDomainError)
    async def handle(request, exc: NutritionDomainError):
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
