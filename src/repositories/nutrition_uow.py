from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base_uow import BaseUnitOfWork
from src.repositories.nutrition import NutritionRepository


class NutritionUnitOfWork(BaseUnitOfWork):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = NutritionRepository(session)
