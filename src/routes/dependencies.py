from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.exceptions import NotFoundError
from src.repositories.user import UserRepository
from src.services.auth import AuthService
from src.services.mail import MailService
from src.services.nutrition import NutritionService

ouath2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(ouath2_scheme), db: AsyncSession = Depends(get_session)):
    payload = AuthService.decode_access_token(token)
    user_id = int(payload.get("sub"))
    current_user = await UserRepository.get_by_id(db, user_id)

    if not current_user:
        raise NotFoundError(resource="User", resource_id=user_id)

    return current_user


async def get_auth_service(db: AsyncSession = Depends(get_session)):
    return AuthService(db, MailService())


async def get_nutrition_service(db: AsyncSession = Depends(get_session)):
    return NutritionService(db)
