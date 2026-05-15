from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core_context.nutrition.contracts.dtos import DailyTotalsDTO
from src.core_context.nutrition.contracts.ports import (
    IDailyTotalsDirectory,
    IMealEntryQueries,
)
from src.core_context.nutrition.infrastructure.orm import DailyDiary, MealEntry


class SqlDailyTotalsDirectory(IDailyTotalsDirectory):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, user_id: int, day: date) -> DailyTotalsDTO | None:
        async with self._session_factory() as session:
            stmt = select(DailyDiary).where(
                DailyDiary.user_id == user_id,
                DailyDiary.target_date == day,
            )
            diary = (await session.execute(stmt)).scalar_one_or_none()
            if diary is None:
                return None

            return DailyTotalsDTO(
                user_id=user_id,
                day=day,
                calories=getattr(diary, "calories", 0.0) or 0.0,
                proteins_g=getattr(diary, "proteins_g", 0.0) or 0.0,
                fats_g=getattr(diary, "fats_g", 0.0) or 0.0,
                carbs_g=getattr(diary, "carbs_g", 0.0) or 0.0,
            )


class SqlMealEntryQueries(IMealEntryQueries):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def count_for_day(self, user_id: int, day: date) -> int:
        async with self._session_factory() as session:
            count = await session.scalar(
                select(func.count(MealEntry.id))
                .select_from(MealEntry)
                .join(DailyDiary, MealEntry.daily_diary_id == DailyDiary.id)
                .where(DailyDiary.user_id == user_id)
                .where(DailyDiary.target_date == day)
            )
            return int(count or 0)
