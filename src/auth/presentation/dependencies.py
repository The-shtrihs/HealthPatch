from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.application.token_utils import PasswordUtils, TokenUtils
from src.auth.application.use_cases.change_password import ChangePasswordUseCase
from src.auth.application.use_cases.login import LoginUseCase
from src.auth.application.use_cases.logout import LogoutUseCase
from src.auth.application.use_cases.oauth import HandleOAuthUserUseCase
from src.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from src.auth.application.use_cases.register import RegisterUseCase
from src.auth.application.use_cases.reset_password import ForgotPasswordUseCase, ResetPasswordUseCase
from src.auth.application.use_cases.two_factor import (
    Confirm2FAUseCase, Disable2FAUseCase, Enable2FAUseCase, Verify2FAAndLoginUseCase,
)
from src.auth.application.use_cases.verify_email import ResendVerificationUseCase, VerifyEmailUseCase
from src.auth.domain.errors import UserInactiveError, UserNotFoundError
from src.auth.domain.models import UserDomain
from src.auth.infrastructure.oauth_state_repository import RedisOAuthStateRepository
from src.auth.infrastructure.repositories import (
    SqlAlchemyRefreshTokenRepository, SqlAlchemyUserRepository,
)
from src.core.constants import DEFAULT_RATE_LIMIT, DEFAULT_RATE_WINDOW_SECONDS
from src.core.database import get_session
from src.core.redis import get_redis
from src.repositories.rate_limit import RateLimitRepository
from src.shared.infrastructure.mail import MailService
from src.shared.infrastructure.totp import TotpService

_security = HTTPBearer()
_pw = PasswordUtils()  


async def get_user_repo(db: AsyncSession = Depends(get_session)):
    return SqlAlchemyUserRepository(db)
 
async def get_token_repo(db: AsyncSession = Depends(get_session)):
    return SqlAlchemyRefreshTokenRepository(db)
 
async def get_mail_service() -> MailService:
    return MailService()

async def get_totp_service() -> TotpService:
    return TotpService()
 
async def get_register_uc(
    user_repo=Depends(get_user_repo),
    mail_service: MailService = Depends(get_mail_service),
) -> RegisterUseCase:
    return RegisterUseCase(user_repo, mail_service, _pw)
 
async def get_login_uc(
    user_repo=Depends(get_user_repo),
    token_repo=Depends(get_token_repo),
) -> LoginUseCase:
    return LoginUseCase(user_repo, token_repo, _pw)
 
async def get_logout_uc(token_repo=Depends(get_token_repo)) -> LogoutUseCase:
    return LogoutUseCase(token_repo)
 
async def get_refresh_uc(
    user_repo=Depends(get_user_repo),
    token_repo=Depends(get_token_repo),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(user_repo, token_repo)
 
async def get_verify_email_uc(
    user_repo=Depends(get_user_repo),
    mail_service: MailService = Depends(get_mail_service),
) -> VerifyEmailUseCase:
    return VerifyEmailUseCase(user_repo, mail_service)
 
async def get_resend_verification_uc(
    user_repo=Depends(get_user_repo),
    mail_service: MailService = Depends(get_mail_service),
) -> ResendVerificationUseCase:
    return ResendVerificationUseCase(user_repo, mail_service)
 
async def get_forgot_password_uc(
    user_repo=Depends(get_user_repo),
    mail_service: MailService = Depends(get_mail_service),
) -> ForgotPasswordUseCase:
    return ForgotPasswordUseCase(user_repo, mail_service)
 
async def get_reset_password_uc(
    user_repo=Depends(get_user_repo),
    token_repo=Depends(get_token_repo),
    mail_service: MailService = Depends(get_mail_service),
) -> ResetPasswordUseCase:
    return ResetPasswordUseCase(user_repo, token_repo, mail_service, _pw)
 
async def get_change_password_uc(
    user_repo=Depends(get_user_repo),
    token_repo=Depends(get_token_repo),
) -> ChangePasswordUseCase:
    return ChangePasswordUseCase(user_repo, token_repo, _pw)
 
async def get_enable_2fa_uc(user_repo=Depends(get_user_repo), totp_service: TotpService = Depends(get_totp_service)) -> Enable2FAUseCase:
    return Enable2FAUseCase(user_repo, totp_service)
 
async def get_confirm_2fa_uc(user_repo=Depends(get_user_repo), totp_service: TotpService = Depends(get_totp_service)) -> Confirm2FAUseCase:
    return Confirm2FAUseCase(user_repo, totp_service)
 
async def get_disable_2fa_uc(user_repo=Depends(get_user_repo), totp_service: TotpService = Depends(get_totp_service)) -> Disable2FAUseCase:
    return Disable2FAUseCase(user_repo, totp_service)
 
async def get_verify_2fa_uc(
    user_repo=Depends(get_user_repo),
    token_repo=Depends(get_token_repo),
    totp_service: TotpService = Depends(get_totp_service)
) -> Verify2FAAndLoginUseCase:
    return Verify2FAAndLoginUseCase(user_repo, token_repo, totp_service)
 
async def get_oauth_uc(
    user_repo=Depends(get_user_repo),
    token_repo=Depends(get_token_repo),
) -> HandleOAuthUserUseCase:
    return HandleOAuthUserUseCase(user_repo, token_repo)
 
 
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    user_repo=Depends(get_user_repo),
) -> UserDomain:
 
    payload = TokenUtils.decode_access_token(credentials.credentials)
    user = await user_repo.get_by_id(int(payload["sub"]))
    if not user:
        raise UserNotFoundError(int(payload["sub"]))
    if not user.is_active:
        raise UserInactiveError()
    return user
 
 
def make_rate_limiter(limit: int = DEFAULT_RATE_LIMIT, window: int = DEFAULT_RATE_WINDOW_SECONDS):
    async def dep(request: Request, redis=Depends(get_redis)):
        from fastapi import HTTPException, status
        repo = RateLimitRepository(redis)
        result = await repo.check(
            identifier=f"ip:{request.client.host}:{request.url.path}",
            limit=limit, window=window,
        )
        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(result.retry_after)},
            )
    return dep

async def get_oauth_state_repo(redis=Depends(get_redis)) -> RedisOAuthStateRepository:
    return RedisOAuthStateRepository(redis)


async def get_handle_oauth_uc(
    db=Depends(get_session),
    token_db=Depends(get_session),
) -> HandleOAuthUserUseCase:
    return HandleOAuthUserUseCase(
        user_repo=SqlAlchemyUserRepository(db),
        token_repo=SqlAlchemyRefreshTokenRepository(token_db),
    )
