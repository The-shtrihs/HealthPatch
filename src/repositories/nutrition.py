from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.nutrition import DailyDiary, Food, MealEntry
from src.models.user import UserProfile


class NutritionRepository:
    @staticmethod
    async def get_user_profile(db: AsyncSession, user_id: int) -> UserProfile | None:
        result = await db.scalars(select(UserProfile).where(UserProfile.user_id == user_id))
        return result.first()

    @staticmethod
    async def get_or_create_daily_diary(db: AsyncSession, user_id: int, target_date: date) -> DailyDiary:
        stmt = (
            insert(DailyDiary)
            .values(user_id=user_id, target_date=target_date, water_ml=0)
            .on_conflict_do_nothing(index_elements=["user_id", "target_date"])
            .returning(DailyDiary.id)
        )
        inserted_id = (await db.execute(stmt)).scalar_one_or_none()
        if inserted_id is not None:
            diary = await db.get(DailyDiary, inserted_id)
            if diary is not None:
                return diary

        result = await db.scalars(select(DailyDiary).where(and_(DailyDiary.user_id == user_id, DailyDiary.target_date == target_date)))
        diary = result.first()
        return diary

    @staticmethod
    async def update_daily_diary(
        db: AsyncSession,
        user_id: int,
        target_date: date,
        water_ml: int | None,
        notes: str | None,
    ) -> DailyDiary:
        diary = await NutritionRepository.get_or_create_daily_diary(db, user_id, target_date)

        if water_ml is not None:
            diary.water_ml = water_ml
        if notes is not None:
            diary.notes = notes
        await db.flush()
        await db.refresh(diary)
        return diary

    @staticmethod
    async def add_meal_entry(
        db: AsyncSession,
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
        db.add(entry)
        await db.flush()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def get_user_meal_entry_with_target_date(
        db: AsyncSession,
        user_id: int,
        meal_entry_id: int,
    ) -> tuple[MealEntry, date] | None:
        stmt = (
            select(MealEntry, DailyDiary.target_date)
            .join(DailyDiary, DailyDiary.id == MealEntry.daily_diary_id)
            .where(and_(MealEntry.id == meal_entry_id, DailyDiary.user_id == user_id))
        )
        row = (await db.execute(stmt)).first()
        if row is None:
            return None
        return row[0], row[1]

    @staticmethod
    async def delete_meal_entry(db: AsyncSession, meal_entry: MealEntry) -> None:
        await db.delete(meal_entry)
        await db.flush()

    @staticmethod
    async def get_day_consumed_totals(db: AsyncSession, user_id: int, target_date: date) -> dict[str, float]:
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

        row = (await db.execute(stmt)).one()
        return {
            "calories": float(row.calories),
            "protein_g": float(row.protein_g),
            "fat_g": float(row.fat_g),
            "carbs_g": float(row.carbs_g),
        }
