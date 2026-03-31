from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.exceptions import NotFoundError
from src.core.redis import get_redis
from src.repositories.activity_uow import ActivityUnitOfWork
from src.repositories.cache import CacheRepository
from src.repositories.oauth_state import OAuthStateRepository
from src.repositories.rate_limit import RateLimitRepository
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.user import UserRepository
from src.services.activity import ActivityService
from src.services.auth import AuthService
from src.services.mail import MailService
from src.services.nutrition import NutritionService
from src.services.oauth import OAuthService
from src.services.totp import TotpService

security = HTTPBearer()


async def get_user_repo(db: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(db)


async def get_refresh_token_repo(db: AsyncSession = Depends(get_session)) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


async def get_oauth_state_repo(redis=Depends(get_redis)):
    return OAuthStateRepository(redis)


async def get_mail_service():
    return MailService()


async def get_totp_service():
    return TotpService()


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repo),
    mail_service: MailService = Depends(get_mail_service),
    totp_service: TotpService = Depends(get_totp_service),
) -> AuthService:
    return AuthService(user_repo, token_repo, mail_service, totp_service)


async def get_oauth_service(
    auth_service: AuthService = Depends(get_auth_service),
    oauth_state_repo: OAuthStateRepository = Depends(get_oauth_state_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> OAuthService:
    return OAuthService(auth_service, oauth_state_repo, user_repo)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), user_repo: UserRepository = Depends(get_user_repo)):
    payload = AuthService.decode_access_token(credentials.credentials)
    user_id = int(payload.get("sub"))
    current_user = await user_repo.get_by_id(user_id)

    if not current_user:
        raise NotFoundError(resource="User", resource_id=user_id)

    return current_user


async def get_nutrition_service(db: AsyncSession = Depends(get_session)):
    return NutritionService(db)


async def get_cache_repo(redis=Depends(get_redis)):
    return CacheRepository(redis)


async def get_rate_limit_repo(redis=Depends(get_redis)):
    return RateLimitRepository(redis)


def make_rate_limiter(limit: int = 60, window: int = 60):

    async def rate_limit_dep(request: Request, rate_limit_repo: RateLimitRepository = Depends(get_rate_limit_repo)):

        identifier = f"ip:{request.client.host}:{request.url.path}"

        result = await rate_limit_repo.check(identifier=identifier, limit=limit, window=window)

        if not result.allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(result.retry_after)},
            )

    return rate_limit_dep


async def get_activity_uow(db: AsyncSession = Depends(get_session)) -> ActivityUnitOfWork:
    return ActivityUnitOfWork(db)


async def get_activity_service(uow: ActivityUnitOfWork = Depends(get_activity_uow)) -> ActivityService:
    return ActivityService(uow)
