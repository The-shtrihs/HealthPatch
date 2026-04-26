from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User
from src.user.application.read_models import FullProfileReadModel
from src.user.infrastructure.mapper import _orm_to_full_profile_rm


class SqlAlchemyUserProfileReadRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_full_profile(self, user_id: int) -> FullProfileReadModel | None:
        result = await self._db.scalars(select(User).where(User.id == user_id).options(selectinload(User.profile)))
        user = result.first()
        return _orm_to_full_profile_rm(user) if user else None
