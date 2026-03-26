from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.nutrition import DailyDiary, Food, MealEntry
from src.models.user import UserProfile


class NutritionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_profile(self, user_id: int) -> UserProfile | None:
        result = await self.db.scalars(select(UserProfile).where(UserProfile.user_id == user_id))
        return result.first()

    async def get_or_create_daily_diary(self, user_id: int, target_date: date) -> DailyDiary:
        stmt = (
            insert(DailyDiary)
            .values(user_id=user_id, target_date=target_date, water_ml=0)
            .on_conflict_do_nothing(index_elements=["user_id", "target_date"])
            .returning(DailyDiary.id)
        )
        inserted_id = (await self.db.execute(stmt)).scalar_one_or_none()
        if inserted_id is not None:
            diary = await self.db.get(DailyDiary, inserted_id)
            if diary is not None:
                return diary

        result = await self.db.scalars(select(DailyDiary).where(and_(DailyDiary.user_id == user_id, DailyDiary.target_date == target_date)))
        diary = result.first()
        return diary

    async def update_daily_diary(
        self,
        user_id: int,
        target_date: date,
        water_ml: int | None,
        notes: str | None,
    ) -> DailyDiary:
        diary = await self.get_or_create_daily_diary(user_id, target_date)

        if water_ml is not None:
            diary.water_ml = water_ml
        if notes is not None:
            diary.notes = notes
        await self.db.flush()
        await self.db.refresh(diary)
        return diary

    async def add_meal_entry(
        self,
        diary_id: int,
        food_id: int,
        meal_type: str,
        weight_grams: float,
    ) -> MealEntry:
        entry = MealEntry(
            daily_diary_id=diary_id,
            food_id=food_id,
            meal_type=meal_type,
            weight_grams=weight_grams,
        )
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def get_user_meal_entry_with_target_date(
        self,
        user_id: int,
        meal_entry_id: int,
    ) -> tuple[MealEntry, date] | None:
        stmt = (
            select(MealEntry, DailyDiary.target_date)
            .join(DailyDiary, DailyDiary.id == MealEntry.daily_diary_id)
            .where(and_(MealEntry.id == meal_entry_id, DailyDiary.user_id == user_id))
        )
        row = (await self.db.execute(stmt)).first()
        if row is None:
            return None
        return row[0], row[1]

    async def delete_meal_entry(self, meal_entry: MealEntry) -> None:
        await self.db.delete(meal_entry)
        await self.db.flush()

    async def get_day_consumed_totals(self, user_id: int, target_date: date) -> dict[str, float]:
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

        row = (await self.db.execute(stmt)).one()
        return {
            "calories": float(row.calories),
            "protein_g": float(row.protein_g),
            "fat_g": float(row.fat_g),
            "carbs_g": float(row.carbs_g),
        }
