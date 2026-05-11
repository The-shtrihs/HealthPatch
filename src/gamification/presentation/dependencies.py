from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.gamification.application.handlers.get_profile import (
    GetGamificationProfileQueryHandler,
)
from src.gamification.domain.interfaces import IGamificationRepository
from src.gamification.infrastructure.repositories import GamificationRepository


def get_gamification_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IGamificationRepository:
    return GamificationRepository(session)


GamificationRepositoryDep = Annotated[
    IGamificationRepository,
    Depends(get_gamification_repository),
]


def get_profile_query_handler(
    repository: GamificationRepositoryDep,
) -> GetGamificationProfileQueryHandler:
    return GetGamificationProfileQueryHandler(repository)


ProfileQueryHandlerDep = Annotated[
    GetGamificationProfileQueryHandler,
    Depends(get_profile_query_handler),
]
