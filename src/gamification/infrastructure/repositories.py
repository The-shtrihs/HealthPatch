from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gamification.domain.interfaces import IGamificationRepository
from src.models.gamification import GamificationProfile
from src.models.nutrition import DailyDiary, MealEntry


class GamificationRepository(IGamificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_by_user_id(self, user_id: int) -> GamificationProfile | None:
        stmt = select(GamificationProfile).where(GamificationProfile.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def ensure_profile(self, user_id: int) -> None:
        profile = await self._get_by_user_id(user_id)
        if profile is None:
            self._session.add(GamificationProfile(user_id=user_id, total_xp=0))

    async def award_xp(self, user_id: int, xp: int) -> int:
        await self.ensure_profile(user_id)
        profile = await self._get_by_user_id(user_id)
        if profile is None:
            raise RuntimeError(f"Gamification profile was not created for user_id={user_id}")

        profile.total_xp += xp
        return profile.total_xp

    async def count_meal_entries_for_day(self, user_id: int, target_date: date) -> int:
        count = await self._session.scalar(
            select(func.count(MealEntry.id))
            .select_from(MealEntry)
            .join(DailyDiary, MealEntry.daily_diary_id == DailyDiary.id)
            .where(DailyDiary.user_id == user_id)
            .where(DailyDiary.target_date == target_date)
        )
        return int(count or 0)
