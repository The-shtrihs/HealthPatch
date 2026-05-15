from sqlalchemy.ext.asyncio import AsyncSession

from src.core_context.gamification.infrastructure.repositories import GamificationRepository
from src.shared.infrastructure.base_uow import BaseUnitOfWork


class GamificationUnitOfWork(BaseUnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.profiles = GamificationRepository(session)
