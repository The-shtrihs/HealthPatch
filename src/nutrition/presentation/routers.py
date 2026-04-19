from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, status

from src.auth.domain.models import UserDomain
from src.auth.presentation.dependencies import get_current_user
from src.nutrition.application.dto import (
	AddMealEntryCommand,
	DeleteMealEntryCommand,
	GetDayOverviewQuery,
	UpdateDailyDiaryCommand,
)
from src.nutrition.application.use_cases import NutritionUseCases
from src.nutrition.presentation.dependencies import get_nutrition_use_cases
from src.nutrition.presentation.schemas import (
	AddMealEntryRequest,
	AddMealEntryResponse,
	DailyNormResponse,
	DayOverviewResponse,
	DeleteMealEntryResponse,
	UpdateDailyDiaryRequest,
	UpdateDailyDiaryResponse,
)

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])


@router.get("/norm", response_model=DailyNormResponse)
async def get_daily_norm(
	nutrition_use_cases: NutritionUseCases = Depends(get_nutrition_use_cases),
	current_user: UserDomain = Depends(get_current_user),
):
	result = await nutrition_use_cases.get_daily_norm(current_user.id)
	return DailyNormResponse(
		calories=result.calories,
		protein_g=result.protein_g,
		fat_g=result.fat_g,
		carbs_g=result.carbs_g,
	)


@router.get("/overview", response_model=DayOverviewResponse)
async def get_day_overview(
	target_date: date | None = None,
	nutrition_use_cases: NutritionUseCases = Depends(get_nutrition_use_cases),
	current_user: UserDomain = Depends(get_current_user),
):
	day = target_date or datetime.now(UTC).date()
	result = await nutrition_use_cases.get_day_overview(GetDayOverviewQuery(user_id=current_user.id, target_date=day))
	return DayOverviewResponse(
		target_date=result.target_date,
		norm=DailyNormResponse(
			calories=result.norm.calories,
			protein_g=result.norm.protein_g,
			fat_g=result.norm.fat_g,
			carbs_g=result.norm.carbs_g,
		),
		consumed=DailyNormResponse(
			calories=result.consumed.calories,
			protein_g=result.consumed.protein_g,
			fat_g=result.consumed.fat_g,
			carbs_g=result.consumed.carbs_g,
		),
		remaining=DailyNormResponse(
			calories=result.remaining.calories,
			protein_g=result.remaining.protein_g,
			fat_g=result.remaining.fat_g,
			carbs_g=result.remaining.carbs_g,
		),
	)


@router.post("/entries", response_model=AddMealEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_meal_entry(
	payload: AddMealEntryRequest,
	nutrition_use_cases: NutritionUseCases = Depends(get_nutrition_use_cases),
	current_user: UserDomain = Depends(get_current_user),
):
	result = await nutrition_use_cases.add_meal_entry(
		AddMealEntryCommand(
			user_id=current_user.id,
			food_id=payload.food_id,
			meal_type=payload.meal_type,
			weight_grams=payload.weight_grams,
			target_date=payload.target_date,
		)
	)
	return AddMealEntryResponse(
		meal_entry_id=result.meal_entry_id,
		target_date=result.target_date,
		remaining=DailyNormResponse(
			calories=result.remaining.calories,
			protein_g=result.remaining.protein_g,
			fat_g=result.remaining.fat_g,
			carbs_g=result.remaining.carbs_g,
		),
	)


@router.delete("/entries/{meal_entry_id}", response_model=DeleteMealEntryResponse)
async def delete_meal_entry(
	meal_entry_id: int,
	nutrition_use_cases: NutritionUseCases = Depends(get_nutrition_use_cases),
	current_user: UserDomain = Depends(get_current_user),
):
	result = await nutrition_use_cases.delete_meal_entry(DeleteMealEntryCommand(user_id=current_user.id, meal_entry_id=meal_entry_id))
	return DeleteMealEntryResponse(
		deleted_meal_entry_id=result.deleted_meal_entry_id,
		target_date=result.target_date,
		remaining=DailyNormResponse(
			calories=result.remaining.calories,
			protein_g=result.remaining.protein_g,
			fat_g=result.remaining.fat_g,
			carbs_g=result.remaining.carbs_g,
		),
	)


@router.patch("/diary", response_model=UpdateDailyDiaryResponse)
async def update_daily_diary(
	payload: UpdateDailyDiaryRequest,
	nutrition_use_cases: NutritionUseCases = Depends(get_nutrition_use_cases),
	current_user: UserDomain = Depends(get_current_user),
):
	result = await nutrition_use_cases.update_daily_diary(
		UpdateDailyDiaryCommand(
			user_id=current_user.id,
			target_date=payload.target_date,
			water_ml=payload.water_ml,
			notes=payload.notes,
		)
	)
	return UpdateDailyDiaryResponse(
		id=result.id,
		user_id=result.user_id,
		target_date=result.target_date,
		water_ml=result.water_ml,
		notes=result.notes,
	)
