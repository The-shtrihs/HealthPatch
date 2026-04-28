from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.nutrition import DailyDiary, Food, MealEntry
from src.models.user import UserProfile
from src.nutrition.domain.interfaces import INutritionReadRepository
from src.nutrition.domain.models import MacroTotalsDomain, NutritionProfileDomain
from src.nutrition.infrastructure.mapper import orm_to_nutrition_profile, to_macro_totals


class SqlAlchemyNutritionReadRepository(INutritionReadRepository):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_profile(self, user_id: int) -> NutritionProfileDomain | None:
        result = await self._db.scalars(select(UserProfile).where(UserProfile.user_id == user_id))
        return orm_to_nutrition_profile(result.first())

    async def get_day_consumed_totals(self, user_id: int, target_date: date) -> MacroTotalsDomain:
        factor = MealEntry.weight_grams / 100.0

        stmt = (
            select(
                func.coalesce(func.sum(Food.calories_per_100g * factor), 0.0).label("calories"),
                func.coalesce(func.sum(Food.protein_per_100g * factor), 0.0).label("protein_g"),
                func.coalesce(func.sum(Food.fat_per_100g * factor), 0.0).label("fat_g"),
                func.coalesce(func.sum(Food.carbs_per_100g * factor), 0.0).label("carbs_g"),
            )
            .select_from(DailyDiary)
            .join(MealEntry, MealEntry.daily_diary_id == DailyDiary.id)
            .join(Food, Food.id == MealEntry.food_id)
            .where(and_(DailyDiary.user_id == user_id, DailyDiary.target_date == target_date))
        )

        row = (await self._db.execute(stmt)).one()
        return to_macro_totals(row)
