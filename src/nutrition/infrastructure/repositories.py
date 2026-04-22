from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.nutrition import DailyDiary, Food, MealEntry
from src.models.user import UserProfile
from src.nutrition.domain.interfaces import INutritionRepository, INutritionUnitOfWork
from src.nutrition.domain.models import MacroTotalsDomain, NutritionProfileDomain
from src.nutrition.infrastructure.mapper import diary_to_dict, orm_to_nutrition_profile, to_macro_totals
from src.shared.infrastructure.base_uow import BaseUnitOfWork


class SqlAlchemyNutritionRepository(INutritionRepository):
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

    async def ensure_daily_diary(self, user_id: int, target_date: date) -> int:
        stmt = (
            insert(DailyDiary)
            .values(user_id=user_id, target_date=target_date, water_ml=0)
            .on_conflict_do_nothing(index_elements=["user_id", "target_date"])
            .returning(DailyDiary.id)
        )
        inserted_id = (await self._db.execute(stmt)).scalar_one_or_none()
        if inserted_id is not None:
            return inserted_id

        result = await self._db.scalars(select(DailyDiary).where(and_(DailyDiary.user_id == user_id, DailyDiary.target_date == target_date)))
        diary = result.first()
        return diary.id

    async def add_meal_entry(self, diary_id: int, food_id: int, meal_type: str, weight_grams: float) -> int:
        entry = MealEntry(
            daily_diary_id=diary_id,
            food_id=food_id,
            meal_type=meal_type,
            weight_grams=weight_grams,
        )
        self._db.add(entry)
        await self._db.flush()
        await self._db.refresh(entry)
        return entry.id

    async def get_user_meal_entry_target_date(self, user_id: int, meal_entry_id: int) -> date | None:
        stmt = (
            select(DailyDiary.target_date)
            .join(MealEntry, DailyDiary.id == MealEntry.daily_diary_id)
            .where(and_(MealEntry.id == meal_entry_id, DailyDiary.user_id == user_id))
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def delete_meal_entry(self, meal_entry_id: int) -> None:
        meal_entry = await self._db.get(MealEntry, meal_entry_id)
        if meal_entry is None:
            return
        await self._db.delete(meal_entry)
        await self._db.flush()

    async def update_daily_diary(self, user_id: int, target_date: date, water_ml: int | None, notes: str | None) -> dict:
        diary_id = await self.ensure_daily_diary(user_id, target_date)
        diary = await self._db.get(DailyDiary, diary_id)

        if water_ml is not None:
            diary.water_ml = water_ml
        if notes is not None:
            diary.notes = notes

        await self._db.flush()
        await self._db.refresh(diary)
        return diary_to_dict(diary)


class SqlAlchemyNutritionUnitOfWork(BaseUnitOfWork, INutritionUnitOfWork):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = SqlAlchemyNutritionRepository(session)
