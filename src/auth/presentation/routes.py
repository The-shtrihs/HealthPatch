from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

from src.auth.application.commands import (
    Confirm2FACommand,
    Disable2FACommand,
    Enable2FACommand,
    ForgotPasswordCommand,
    LogoutAllCommand,
    ResendVerificationCommand,
    VerifyEmailCommand,
)
from src.auth.application.handlers.change_password import ChangePasswordCommandHandler
from src.auth.application.handlers.get_me import GetMeQueryHandler
from src.auth.application.handlers.login import LoginCommandHandler
from src.auth.application.handlers.logout import LogoutCommandHandler
from src.auth.application.handlers.refresh_token import RefreshTokenCommandHandler
from src.auth.application.handlers.register import RegisterCommandHandler
from src.auth.application.handlers.reset_password import ForgotPasswordCommandHandler, ResetPasswordCommandHandler
from src.auth.application.handlers.two_factor import (
    Confirm2FACommandHandler,
    Disable2FACommandHandler,
    Enable2FACommandHandler,
    Verify2FAAndLoginCommandHandler,
)
from src.auth.application.handlers.verify_email import ResendVerificationCommandHandler, VerifyEmailCommandHandler
from src.auth.application.queries import GetMeQuery
from src.auth.domain.models import UserDomain
from src.auth.presentation.dependencies import (
    get_change_password_handler,
    get_confirm_2fa_handler,
    get_current_user,
    get_disable_2fa_handler,
    get_enable_2fa_handler,
    get_forgot_password_handler,
    get_get_me_handler,
    get_login_handler,
    get_logout_handler,
    get_refresh_handler,
    get_register_handler,
    get_resend_verification_handler,
    get_reset_password_handler,
    get_verify_2fa_handler,
    get_verify_email_handler,
    make_rate_limiter,
)
from src.auth.presentation.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    TwoFactorSetupResponse,
    UserMeResponse,
    Verify2FARequest,
)
from src.core.constants import DEFAULT_RATE_LIMIT

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    handler: RegisterCommandHandler = Depends(get_register_handler),
    _rl=Depends(make_rate_limiter(limit=DEFAULT_RATE_LIMIT, window=3600)),
):
    await handler.handle(data.to_command(), background_tasks)
    return MessageResponse(message="User registered successfully. Please check your email to verify your account.")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    data: LoginRequest,
    handler: LoginCommandHandler = Depends(get_login_handler),
    _rl=Depends(make_rate_limiter(limit=DEFAULT_RATE_LIMIT, window=60)),
):
    device_info = f"{request.headers.get('user-agent', 'unknown')} - {request.client.host}"
    result = await handler.handle(data.to_command(device_info=device_info))
    return TokenResponse.model_validate(result)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    handler: RefreshTokenCommandHandler = Depends(get_refresh_handler),
):
    result = await handler.handle(data.to_refresh_command())
    return TokenResponse.model_validate(result)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshRequest,
    handler: LogoutCommandHandler = Depends(get_logout_handler),
):
    await handler.handle(data.to_logout_command())
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    current_user: UserDomain = Depends(get_current_user),
    handler: LogoutCommandHandler = Depends(get_logout_handler),
):
    await handler.handle_all(LogoutAllCommand(user_id=current_user.id))
    return MessageResponse(message="Logged out from all sessions successfully")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: UserDomain = Depends(get_current_user),
    handler: ChangePasswordCommandHandler = Depends(get_change_password_handler),
):
    await handler.handle(data.to_command(user_id=current_user.id))
    return MessageResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    handler: ForgotPasswordCommandHandler = Depends(get_forgot_password_handler),
    _rl=Depends(make_rate_limiter(limit=3, window=3600)),
):
    await handler.handle(ForgotPasswordCommand(email=email), background_tasks)
    return MessageResponse(message="If an account with that email exists, a password reset link has been sent")


@router.post("/resend-verification-email", response_model=MessageResponse)
async def resend_verification_email(
    email: str,
    background_tasks: BackgroundTasks,
    handler: ResendVerificationCommandHandler = Depends(get_resend_verification_handler),
    _rl=Depends(make_rate_limiter(limit=3, window=3600)),
):
    await handler.handle(ResendVerificationCommand(email=email), background_tasks)
    return MessageResponse(message="If an account with that email exists and is not verified, a verification email has been resent")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    token: str,
    handler: VerifyEmailCommandHandler = Depends(get_verify_email_handler),
):
    await handler.handle(VerifyEmailCommand(token=token))
    return MessageResponse(message="Email verified successfully")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    token: str,
    data: ChangePasswordRequest,
    handler: ResetPasswordCommandHandler = Depends(get_reset_password_handler),
):
    await handler.handle(data.to_reset_command(token=token))
    return MessageResponse(message="Password reset successfully")


@router.post("/enable-2fa", response_model=TwoFactorSetupResponse)
async def enable_2fa(
    current_user: UserDomain = Depends(get_current_user),
    handler: Enable2FACommandHandler = Depends(get_enable_2fa_handler),
):
    result = await handler.handle(Enable2FACommand(user_id=current_user.id))
    return TwoFactorSetupResponse.model_validate(result)


@router.post("/confirm-2fa", response_model=MessageResponse)
async def confirm_2fa(
    code: str,
    current_user: UserDomain = Depends(get_current_user),
    handler: Confirm2FACommandHandler = Depends(get_confirm_2fa_handler),
):
    await handler.handle(Confirm2FACommand(user_id=current_user.id, code=code))
    return MessageResponse(message="2FA has been enabled successfully")


@router.post("/disable-2fa", response_model=MessageResponse)
async def disable_2fa(
    code: str,
    current_user: UserDomain = Depends(get_current_user),
    handler: Disable2FACommandHandler = Depends(get_disable_2fa_handler),
):
    await handler.handle(Disable2FACommand(user_id=current_user.id, code=code))
    return MessageResponse(message="2FA has been disabled successfully")


@router.post("/verify-2fa", response_model=TokenResponse)
async def verify_2fa(
    request: Request,
    data: Verify2FARequest,
    handler: Verify2FAAndLoginCommandHandler = Depends(get_verify_2fa_handler),
    _rl=Depends(make_rate_limiter(limit=5, window=60)),
):
    device_info = f"{request.headers.get('user-agent', 'unknown')} - {request.client.host}"
    result = await handler.handle(data.to_command(device_info=device_info))
    return TokenResponse.model_validate(result)


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    current_user: UserDomain = Depends(get_current_user),
    handler: GetMeQueryHandler = Depends(get_get_me_handler),
):
    result = handler.handle(GetMeQuery(user=current_user))
    return UserMeResponse.model_validate(result)
