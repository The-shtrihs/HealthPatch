from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.application.handlers.change_password import ChangePasswordCommandHandler
from src.auth.application.handlers.login import LoginCommandHandler
from src.auth.application.handlers.logout import LogoutCommandHandler
from src.auth.application.handlers.oauth import HandleOAuthUserCommandHandler
from src.auth.application.handlers.refresh_token import RefreshTokenCommandHandler
from src.auth.application.handlers.register import RegisterCommandHandler
from src.auth.application.handlers.reset_password import ForgotPasswordCommandHandler, ResetPasswordCommandHandler
from src.auth.application.handlers.two_factor import (
    Confirm2FACommandHandler, Disable2FACommandHandler,
    Enable2FACommandHandler, Verify2FAAndLoginCommandHandler,
)
from src.auth.application.handlers.verify_email import ResendVerificationCommandHandler, VerifyEmailCommandHandler
from src.auth.application.handlers.get_me import GetMeQueryHandler
from src.auth.application.token_utils import PasswordUtils, TokenUtils
from src.auth.domain.errors import UserInactiveError, UserNotFoundError
from src.auth.domain.models import UserDomain
from src.auth.infrastructure.repositories import SqlAlchemyRefreshTokenRepository, SqlAlchemyUserRepository
from src.core.constants import DEFAULT_RATE_LIMIT, DEFAULT_RATE_WINDOW_SECONDS
from src.core.database import get_session
from src.core.redis import get_redis
from src.repositories.rate_limit import RateLimitRepository
from src.shared.infrastructure.mail import MailService
from src.shared.infrastructure.totp import TotpService
from src.auth.infrastructure.oauth_state_repository import RedisOAuthStateRepository

_security = HTTPBearer()
_pw = PasswordUtils()

async def get_user_repo(db: AsyncSession = Depends(get_session)): return SqlAlchemyUserRepository(db)
async def get_token_repo(db: AsyncSession = Depends(get_session)): return SqlAlchemyRefreshTokenRepository(db)
async def get_mail_service() -> MailService: return MailService()
async def get_totp_service() -> TotpService: return TotpService()
async def get_oauth_state_repo(redis=Depends(get_redis)) -> RedisOAuthStateRepository:
    return RedisOAuthStateRepository(redis)

async def get_register_handler(user_repo=Depends(get_user_repo), mail_service=Depends(get_mail_service)) -> RegisterCommandHandler:
    return RegisterCommandHandler(user_repo, mail_service, _pw)

async def get_login_handler(user_repo=Depends(get_user_repo), token_repo=Depends(get_token_repo)) -> LoginCommandHandler:
    return LoginCommandHandler(user_repo, token_repo, _pw)

async def get_logout_handler(token_repo=Depends(get_token_repo)) -> LogoutCommandHandler:
    return LogoutCommandHandler(token_repo)

async def get_refresh_handler(user_repo=Depends(get_user_repo), token_repo=Depends(get_token_repo)) -> RefreshTokenCommandHandler:
    return RefreshTokenCommandHandler(user_repo, token_repo)

async def get_change_password_handler(user_repo=Depends(get_user_repo), token_repo=Depends(get_token_repo)) -> ChangePasswordCommandHandler:
    return ChangePasswordCommandHandler(user_repo, token_repo, _pw)

async def get_forgot_password_handler(user_repo=Depends(get_user_repo), mail_service=Depends(get_mail_service)) -> ForgotPasswordCommandHandler:
    return ForgotPasswordCommandHandler(user_repo, mail_service)

async def get_reset_password_handler(user_repo=Depends(get_user_repo), token_repo=Depends(get_token_repo), mail_service=Depends(get_mail_service)) -> ResetPasswordCommandHandler:
    return ResetPasswordCommandHandler(user_repo, token_repo, mail_service, _pw)

async def get_verify_email_handler(user_repo=Depends(get_user_repo), mail_service=Depends(get_mail_service)) -> VerifyEmailCommandHandler:
    return VerifyEmailCommandHandler(user_repo, mail_service)

async def get_resend_verification_handler(user_repo=Depends(get_user_repo), mail_service=Depends(get_mail_service)) -> ResendVerificationCommandHandler:
    return ResendVerificationCommandHandler(user_repo, mail_service)

async def get_enable_2fa_handler(user_repo=Depends(get_user_repo), totp_service=Depends(get_totp_service)) -> Enable2FACommandHandler:
    return Enable2FACommandHandler(user_repo, totp_service)

async def get_confirm_2fa_handler(user_repo=Depends(get_user_repo), totp_service=Depends(get_totp_service)) -> Confirm2FACommandHandler:
    return Confirm2FACommandHandler(user_repo, totp_service)

async def get_disable_2fa_handler(user_repo=Depends(get_user_repo), totp_service=Depends(get_totp_service)) -> Disable2FACommandHandler:
    return Disable2FACommandHandler(user_repo, totp_service)

async def get_verify_2fa_handler(user_repo=Depends(get_user_repo), token_repo=Depends(get_token_repo), totp_service=Depends(get_totp_service)) -> Verify2FAAndLoginCommandHandler:
    return Verify2FAAndLoginCommandHandler(user_repo, token_repo, totp_service)

async def get_oauth_handler(user_repo=Depends(get_user_repo), token_repo=Depends(get_token_repo)) -> HandleOAuthUserCommandHandler:
    return HandleOAuthUserCommandHandler(user_repo, token_repo)

async def get_get_me_handler() -> GetMeQueryHandler:
    return GetMeQueryHandler()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    user_repo=Depends(get_user_repo),
) -> UserDomain:
    payload = TokenUtils.decode_access_token(credentials.credentials)
    user = await user_repo.get_by_id(int(payload["sub"]))
    if not user: raise UserNotFoundError(int(payload["sub"]))
    if not user.is_active: raise UserInactiveError()
    return user

def make_rate_limiter(limit: int = DEFAULT_RATE_LIMIT, window: int = DEFAULT_RATE_WINDOW_SECONDS):
    async def dep(request: Request, redis=Depends(get_redis)):
        from fastapi import HTTPException, status
        repo = RateLimitRepository(redis)
        result = await repo.check(identifier=f"ip:{request.client.host}:{request.url.path}", limit=limit, window=window)
        if not result.allowed:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.", headers={"Retry-After": str(result.retry_after)})
    return dep