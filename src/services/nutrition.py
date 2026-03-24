from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BadRequestError, NotFoundError
from src.repositories.nutrition import NutritionRepository
from src.services.nutrition_calculators import calculate_daily_norm


class NutritionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_daily_norm(self, user_id: int) -> dict[str, float]:
        profile = await self._get_validated_profile(user_id)
        return calculate_daily_norm(profile)

    async def get_day_overview(self, user_id: int, target_date: date) -> dict:
        norm = await self.get_daily_norm(user_id)
        consumed = await NutritionRepository.get_day_consumed_totals(self.db, user_id, target_date)

        remaining = {
            "calories": max(0.0, norm["calories"] - consumed["calories"]),
            "protein_g": max(0.0, norm["protein_g"] - consumed["protein_g"]),
            "fat_g": max(0.0, norm["fat_g"] - consumed["fat_g"]),
            "carbs_g": max(0.0, norm["carbs_g"] - consumed["carbs_g"]),
        }

        return {
            "target_date": target_date,
            "norm": norm,
            "consumed": consumed,
            "remaining": remaining,
        }

    async def add_meal_entry_and_recalculate(
        self,
        user_id: int,
        food_id: int,
        meal_type: str,
        weight_grams: float,
        target_date: date | None = None,
    ) -> dict:
        if weight_grams <= 0:
            raise BadRequestError(message="Meal weight must be greater than 0")

        meal_type = meal_type.strip()
        if not meal_type:
            raise BadRequestError(message="Meal type is required")

        day = target_date or datetime.now(UTC).date()
        async with self.db.begin():
            await self._get_validated_profile(user_id)

            diary = await NutritionRepository.get_or_create_daily_diary(self.db, user_id, day)

            meal_entry = await NutritionRepository.add_meal_entry(
                db=self.db,
                diary_id=diary.id,
                food_id=food_id,
                meal_type=meal_type,
                weight_grams=weight_grams,
            )

            overview = await self.get_day_overview(user_id, day)
            return {
                "meal_entry_id": meal_entry.id,
                "target_date": day,
                "remaining": overview["remaining"],
            }

    async def delete_meal_entry_and_recalculate(self, user_id: int, meal_entry_id: int) -> dict:
        async with self.db.begin():
            await self._get_validated_profile(user_id)

            row = await NutritionRepository.get_user_meal_entry_with_target_date(self.db, user_id, meal_entry_id)
            if row is None:
                raise NotFoundError(resource="Meal entry", resource_id=meal_entry_id)

            meal_entry, target_date = row
            await NutritionRepository.delete_meal_entry(self.db, meal_entry)

            overview = await self.get_day_overview(user_id, target_date)
            return {
                "deleted_meal_entry_id": meal_entry_id,
                "target_date": target_date,
                "remaining": overview["remaining"],
            }

    async def update_daily_diary(self, user_id: int, target_date: date, water_ml: int | None, notes: str | None):
        async with self.db.begin():
            return await NutritionRepository.update_daily_diary(
                db=self.db,
                user_id=user_id,
                target_date=target_date,
                water_ml=water_ml,
                notes=notes,
            )

    async def _get_validated_profile(self, user_id: int):
        profile = await NutritionRepository.get_user_profile(self.db, user_id)

        if not profile:
            raise NotFoundError(resource="User profile")

        missing_fields = []
        if profile.age is None:
            missing_fields.append("age")
        if profile.weight is None:
            missing_fields.append("weight")
        if profile.height is None:
            missing_fields.append("height")
        if profile.gender is None:
            missing_fields.append("gender")
        if profile.fitness_goal is None:
            missing_fields.append("fitness_goal")

        if missing_fields:
            raise BadRequestError(message=(f"Complete profile is required for nutrition calculations. Missing: {', '.join(missing_fields)}"))

        return profile
