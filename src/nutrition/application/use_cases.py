from datetime import UTC, datetime
from typing import Any

from src.nutrition.application.dto import (
    AddMealEntryCommand,
    AddMealEntryResult,
    DayOverviewDto,
    DeleteMealEntryCommand,
    DeleteMealEntryResult,
    GetDayOverviewQuery,
    MacroTotalsDto,
    UpdateDailyDiaryCommand,
    UpdateDailyDiaryResult,
)
from src.nutrition.domain.errors import (
    MealEntryNotFoundError,
    NutritionProfileNotFoundError,
)
from src.nutrition.domain.factory import calculate_daily_norm
from src.nutrition.domain.interfaces import INutritionUnitOfWork
from src.nutrition.domain.models import MealEntryCreateDomain, NutritionProfileDomain


class NutritionUseCases:
    def __init__(self, uow: INutritionUnitOfWork):
        self._uow = uow

    async def get_daily_norm(self, user_id: int) -> MacroTotalsDto:
        profile = await self._require_profile(user_id)
        norm = self._safe_calculate_daily_norm(profile)
        return self._to_macro_dto(norm)

    async def get_day_overview(self, query: GetDayOverviewQuery) -> DayOverviewDto:
        profile = await self._require_profile(query.user_id)

        norm = self._safe_calculate_daily_norm(profile)
        consumed = await self._uow.repo.get_day_consumed_totals(query.user_id, query.target_date)
        remaining = norm.remaining_after(consumed)

        return DayOverviewDto(
            target_date=query.target_date,
            norm=self._to_macro_dto(norm),
            consumed=self._to_macro_dto(consumed),
            remaining=self._to_macro_dto(remaining),
        )

    async def add_meal_entry(self, command: AddMealEntryCommand) -> AddMealEntryResult:
        create = MealEntryCreateDomain(
            food_id=command.food_id,
            meal_type=command.meal_type,
            weight_grams=command.weight_grams,
            target_date=command.target_date,
        )

        create.validate()

        meal_type = create.normalized_meal_type()
        day = create.target_date or datetime.now(UTC).date()

        async with self._uow:
            profile = await self._require_profile(command.user_id)

            diary_id = await self._uow.repo.ensure_daily_diary(command.user_id, day)
            meal_entry_id = await self._uow.repo.add_meal_entry(
                diary_id=diary_id,
                food_id=create.food_id,
                meal_type=meal_type,
                weight_grams=create.weight_grams,
            )

            norm = self._safe_calculate_daily_norm(profile)
            consumed = await self._uow.repo.get_day_consumed_totals(command.user_id, day)
            remaining = norm.remaining_after(consumed)

            return AddMealEntryResult(
                meal_entry_id=meal_entry_id,
                target_date=day,
                remaining=self._to_macro_dto(remaining),
            )

    async def delete_meal_entry(self, command: DeleteMealEntryCommand) -> DeleteMealEntryResult:
        async with self._uow:
            profile = await self._require_profile(command.user_id)

            target_date = await self._uow.repo.get_user_meal_entry_target_date(command.user_id, command.meal_entry_id)
            if target_date is None:
                raise MealEntryNotFoundError(command.meal_entry_id)

            await self._uow.repo.delete_meal_entry(command.meal_entry_id)

            norm = self._safe_calculate_daily_norm(profile)
            consumed = await self._uow.repo.get_day_consumed_totals(command.user_id, target_date)
            remaining = norm.remaining_after(consumed)

            return DeleteMealEntryResult(
                deleted_meal_entry_id=command.meal_entry_id,
                target_date=target_date,
                remaining=self._to_macro_dto(remaining),
            )

    async def update_daily_diary(self, command: UpdateDailyDiaryCommand) -> UpdateDailyDiaryResult:
        async with self._uow:
            updated = await self._uow.repo.update_daily_diary(
                user_id=command.user_id,
                target_date=command.target_date,
                water_ml=command.water_ml,
                notes=command.notes,
            )
        return self._to_update_diary_result(updated)

    async def _require_profile(self, user_id: int) -> NutritionProfileDomain:
        profile = await self._uow.repo.get_profile(user_id)
        if profile is None:
            raise NutritionProfileNotFoundError(user_id)
        return profile

    def _safe_calculate_daily_norm(self, profile: NutritionProfileDomain):
        return calculate_daily_norm(profile)

    @staticmethod
    def _to_macro_dto(macro) -> MacroTotalsDto:
        return MacroTotalsDto(
            calories=round(macro.calories, 2),
            protein_g=round(macro.protein_g, 2),
            fat_g=round(macro.fat_g, 2),
            carbs_g=round(macro.carbs_g, 2),
        )

    @staticmethod
    def _to_update_diary_result(raw: Any) -> UpdateDailyDiaryResult:
        if isinstance(raw, dict):
            return UpdateDailyDiaryResult(
                id=raw["id"],
                user_id=raw["user_id"],
                target_date=raw["target_date"],
                water_ml=raw["water_ml"],
                notes=raw.get("notes"),
            )

        return UpdateDailyDiaryResult(
            id=raw.id,
            user_id=raw.user_id,
            target_date=raw.target_date,
            water_ml=raw.water_ml,
            notes=raw.notes,
        )
