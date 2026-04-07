from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.activity import ActivityRepository
from src.repositories.base_uow import BaseUnitOfWork


class ActivityUnitOfWork(BaseUnitOfWork):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = ActivityRepository(session)
