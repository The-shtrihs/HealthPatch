from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.user.application.handlers.delete_account import DeleteAccountCommandHandler
from src.user.application.handlers.get_profile import GetMyProfileQueryHandler
from src.user.application.handlers.update_fitness import UpdateFitnessCommandHandler
from src.user.application.handlers.update_user_info import UpdateUserInfoCommandHandler
from src.user.infrastructure.repositories import SqlAlchemyUserProfileRepository


async def get_repo(db: AsyncSession = Depends(get_session)):
    return SqlAlchemyUserProfileRepository(db)


async def get_get_profile_handler(repo=Depends(get_repo)) -> GetMyProfileQueryHandler:
    return GetMyProfileQueryHandler(repo)


async def get_update_user_info_handler(repo=Depends(get_repo)) -> UpdateUserInfoCommandHandler:
    return UpdateUserInfoCommandHandler(repo)


async def get_update_fitness_handler(repo=Depends(get_repo)) -> UpdateFitnessCommandHandler:
    return UpdateFitnessCommandHandler(repo)


async def get_delete_account_handler(repo=Depends(get_repo)) -> DeleteAccountCommandHandler:
    return DeleteAccountCommandHandler(repo)
