from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, status

from src.models.user import User
from src.routes.dependencies import get_current_user, get_nutrition_service
from src.schemas.nutrition import (
    AddMealEntryRequest,
    AddMealEntryResponse,
    DailyNormResponse,
    DayOverviewResponse,
    DeleteMealEntryResponse,
    UpdateDailyDiaryRequest,
    UpdateDailyDiaryResponse,
)
from src.services.nutrition import NutritionService

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])


@router.get("/norm", response_model=DailyNormResponse)
async def get_daily_norm(
    nutrition_service: NutritionService = Depends(get_nutrition_service),
    current_user: User = Depends(get_current_user),
):
    return await nutrition_service.get_daily_norm(current_user.id)


@router.get("/overview", response_model=DayOverviewResponse)
async def get_day_overview(
    target_date: date | None = None,
    nutrition_service: NutritionService = Depends(get_nutrition_service),
    current_user: User = Depends(get_current_user),
):
    day = target_date or datetime.now(UTC).date()
    return await nutrition_service.get_day_overview(current_user.id, day)


@router.post("/entries", response_model=AddMealEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_meal_entry(
    payload: AddMealEntryRequest,
    nutrition_service: NutritionService = Depends(get_nutrition_service),
    current_user: User = Depends(get_current_user),
):
    return await nutrition_service.add_meal_entry_and_recalculate(
        user_id=current_user.id,
        food_id=payload.food_id,
        meal_type=payload.meal_type,
        weight_grams=payload.weight_grams,
        target_date=payload.target_date,
    )


@router.delete("/entries/{meal_entry_id}", response_model=DeleteMealEntryResponse)
async def delete_meal_entry(
    meal_entry_id: int,
    nutrition_service: NutritionService = Depends(get_nutrition_service),
    current_user: User = Depends(get_current_user),
):
    return await nutrition_service.delete_meal_entry_and_recalculate(
        user_id=current_user.id,
        meal_entry_id=meal_entry_id,
    )


@router.patch("/diary", response_model=UpdateDailyDiaryResponse)
async def update_daily_diary(
    payload: UpdateDailyDiaryRequest,
    nutrition_service: NutritionService = Depends(get_nutrition_service),
    current_user: User = Depends(get_current_user),
):
    return await nutrition_service.update_daily_diary(
        user_id=current_user.id,
        target_date=payload.target_date,
        water_ml=payload.water_ml,
        notes=payload.notes,
    )
