from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.exceptions import NotFoundError
from src.repositories.user import UserRepository
from src.services.auth import AuthService
from src.services.mail import MailService
from src.services.oauth import OAuthService
from src.services.totp import TotpService

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_session)):
    payload = AuthService.decode_access_token(credentials.credentials)
    user_id = int(payload.get("sub"))
    current_user = await UserRepository.get_by_id(db, user_id)

    if not current_user:
        raise NotFoundError(resource="User", resource_id=user_id)

    return current_user


async def get_auth_service(db: AsyncSession = Depends(get_session)):
    return AuthService(db, MailService(), TotpService())


async def get_oauth_service(db: AsyncSession = Depends(get_session), auth_service: AuthService = Depends(get_auth_service)):
    return OAuthService(db, auth_service)
