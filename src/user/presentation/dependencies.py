from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.user.application.use_cases import UserProfileUseCases
from src.user.infrastructure.repositories import SqlAlchemyUserProfileRepository


async def get_user_profile_use_cases(db: AsyncSession = Depends(get_session)) -> UserProfileUseCases:
    return UserProfileUseCases(SqlAlchemyUserProfileRepository(db))
