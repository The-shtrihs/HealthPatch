from sqlalchemy.ext.asyncio import AsyncSession

from src.activity.domain.interfaces import IActivityUnitOfWork
from src.activity.infrastructure.repositories import SqlAlchemyActivityRepository
from src.shared.infrastructure.base_uow import BaseUnitOfWork


class SqlAlchemyActivityUnitOfWork(BaseUnitOfWork, IActivityUnitOfWork):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo: SqlAlchemyActivityRepository = SqlAlchemyActivityRepository(session)
