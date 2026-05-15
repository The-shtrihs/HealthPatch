from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core_context.user.application.interfaces import IUserProfileReadRepository
from src.core_context.user.application.read_models import FullProfileReadModel
from src.core_context.user.infrastructure.mapper import _orm_to_full_profile_rm
from src.core_context.user.infrastructure.orm import User


class SqlAlchemyUserProfileReadRepository(IUserProfileReadRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_full_profile(self, user_id: int) -> FullProfileReadModel | None:
        result = await self._db.scalars(select(User).where(User.id == user_id).options(selectinload(User.profile)))
        user = result.first()
        return _orm_to_full_profile_rm(user) if user else None
