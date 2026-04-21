from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, status

from src.auth.domain.models import UserDomain
from src.auth.presentation.dependencies import get_current_user
from src.nutrition.application.commands import (
	AddMealEntryCommand,
	DeleteMealEntryCommand,
	UpdateDailyDiaryCommand,
)
from src.nutrition.application.handlers.add_meal_entry import AddMealEntryCommandHandler
from src.nutrition.application.handlers.delete_meal_entry import DeleteMealEntryCommandHandler
from src.nutrition.application.handlers.get_daily_norm import GetDailyNormQueryHandler
from src.nutrition.application.handlers.get_day_overview import GetDayOverviewQueryHandler
from src.nutrition.application.handlers.update_daily_diary import UpdateDailyDiaryCommandHandler
from src.nutrition.application.queries import GetDayOverviewQuery
from src.nutrition.application.queries import GetDailyNormQuery
from src.nutrition.presentation.dependencies import (
	get_add_meal_entry_handler,
	get_delete_meal_entry_handler,
	get_get_daily_norm_handler,
	get_get_day_overview_handler,
	get_update_daily_diary_handler,
)
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
	handler: GetDailyNormQueryHandler = Depends(get_get_daily_norm_handler),
	current_user: UserDomain = Depends(get_current_user),
):
	result = await handler.handle(GetDailyNormQuery(user_id=current_user.id))
	return DailyNormResponse(
		calories=result.calories,
		protein_g=result.protein_g,
		fat_g=result.fat_g,
		carbs_g=result.carbs_g,
	)


@router.get("/overview", response_model=DayOverviewResponse)
async def get_day_overview(
	target_date: date | None = None,
	handler: GetDayOverviewQueryHandler = Depends(get_get_day_overview_handler),
	current_user: UserDomain = Depends(get_current_user),
):
	day = target_date or datetime.now(UTC).date()
	result = await handler.handle(GetDayOverviewQuery(user_id=current_user.id, target_date=day))
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
	handler: AddMealEntryCommandHandler = Depends(get_add_meal_entry_handler),
	current_user: UserDomain = Depends(get_current_user),
):
	meal_entry_id = await handler.handle(
		AddMealEntryCommand(
			user_id=current_user.id,
			food_id=payload.food_id,
			meal_type=payload.meal_type,
			weight_grams=payload.weight_grams,
			target_date=payload.target_date,
		)
	)
	return AddMealEntryResponse(meal_entry_id=meal_entry_id)


@router.delete("/entries/{meal_entry_id}", response_model=DeleteMealEntryResponse)
async def delete_meal_entry(
	meal_entry_id: int,
	handler: DeleteMealEntryCommandHandler = Depends(get_delete_meal_entry_handler),
	current_user: UserDomain = Depends(get_current_user),
):
	deleted_meal_entry_id = await handler.handle(DeleteMealEntryCommand(user_id=current_user.id, meal_entry_id=meal_entry_id))
	return DeleteMealEntryResponse(deleted_meal_entry_id=deleted_meal_entry_id)


@router.patch("/diary", response_model=UpdateDailyDiaryResponse)
async def update_daily_diary(
	payload: UpdateDailyDiaryRequest,
	handler: UpdateDailyDiaryCommandHandler = Depends(get_update_daily_diary_handler),
	current_user: UserDomain = Depends(get_current_user),
):
	diary_id = await handler.handle(
		UpdateDailyDiaryCommand(
			user_id=current_user.id,
			target_date=payload.target_date,
			water_ml=payload.water_ml,
			notes=payload.notes,
		)
	)
	return UpdateDailyDiaryResponse(id=diary_id)
