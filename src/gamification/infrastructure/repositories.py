from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gamification.domain.interfaces import IGamificationRepository
from src.models.gamification import GamificationProfile


class GamificationRepository(IGamificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: int) -> GamificationProfile | None:
        stmt = select(GamificationProfile).where(
            GamificationProfile.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, profile: GamificationProfile) -> None:
        self._session.add(profile)