from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

from src.auth.application.use_cases.change_password import ChangePasswordUseCase
from src.auth.application.use_cases.login import LoginUseCase
from src.auth.application.use_cases.logout import LogoutUseCase
from src.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from src.auth.application.use_cases.register import RegisterUseCase
from src.auth.application.use_cases.reset_password import ForgotPasswordUseCase, ResetPasswordUseCase
from src.auth.application.use_cases.two_factor import (
    Confirm2FAUseCase,
    Disable2FAUseCase,
    Enable2FAUseCase,
    Verify2FAAndLoginUseCase,
)
from src.auth.application.use_cases.verify_email import ResendVerificationUseCase, VerifyEmailUseCase
from src.auth.domain.models import UserDomain
from src.auth.presentation.dependencies import (
    get_change_password_uc,
    get_confirm_2fa_uc,
    get_current_user,
    get_disable_2fa_uc,
    get_enable_2fa_uc,
    get_forgot_password_uc,
    get_login_uc,
    get_logout_uc,
    get_refresh_uc,
    get_register_uc,
    get_resend_verification_uc,
    get_reset_password_uc,
    get_verify_2fa_uc,
    get_verify_email_uc,
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


def _token_response(result) -> TokenResponse:
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    uc: RegisterUseCase = Depends(get_register_uc),
    _rl=Depends(make_rate_limiter(limit=DEFAULT_RATE_LIMIT, window=3600)),
):
    await uc.execute(data.name, data.email, data.password, background_tasks)
    return MessageResponse(message="User registered successfully. Please check your email to verify your account.")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    data: LoginRequest,
    uc: LoginUseCase = Depends(get_login_uc),
    _rl=Depends(make_rate_limiter(limit=DEFAULT_RATE_LIMIT, window=60)),
):
    device_info = f"{request.headers.get('user-agent', 'unknown')} - {request.client.host}"
    return _token_response(await uc.execute(data.email, data.password, device_info))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, uc: RefreshTokenUseCase = Depends(get_refresh_uc)):
    return _token_response(await uc.execute(data.refresh_token))


@router.post("/logout", response_model=MessageResponse)
async def logout(data: RefreshRequest, uc: LogoutUseCase = Depends(get_logout_uc)):
    await uc.execute(data.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    current_user: UserDomain = Depends(get_current_user),
    uc: LogoutUseCase = Depends(get_logout_uc),
):
    await uc.execute_all(current_user.id)
    return MessageResponse(message="Logged out from all sessions successfully")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: UserDomain = Depends(get_current_user),
    uc: ChangePasswordUseCase = Depends(get_change_password_uc),
):
    await uc.execute(current_user.id, data.current_password, data.new_password)
    return MessageResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    uc: ForgotPasswordUseCase = Depends(get_forgot_password_uc),
    _rl=Depends(make_rate_limiter(limit=3, window=3600)),
):
    await uc.execute(email, background_tasks)
    return MessageResponse(message="If an account with that email exists, a password reset link has been sent")


@router.post("/resend-verification-email", response_model=MessageResponse)
async def resend_verification_email(
    email: str,
    background_tasks: BackgroundTasks,
    uc: ResendVerificationUseCase = Depends(get_resend_verification_uc),
    _rl=Depends(make_rate_limiter(limit=3, window=3600)),
):
    await uc.execute(email, background_tasks)
    return MessageResponse(message="If an account with that email exists and is not verified, a verification email has been resent")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(token: str, uc: VerifyEmailUseCase = Depends(get_verify_email_uc)):
    await uc.execute(token)
    return MessageResponse(message="Email verified successfully")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    token: str,
    data: ChangePasswordRequest,
    uc: ResetPasswordUseCase = Depends(get_reset_password_uc),
):
    await uc.execute(token, data.new_password)
    return MessageResponse(message="Password reset successfully")


@router.post("/enable-2fa", response_model=TwoFactorSetupResponse)
async def enable_2fa(
    current_user: UserDomain = Depends(get_current_user),
    uc: Enable2FAUseCase = Depends(get_enable_2fa_uc),
):
    result = await uc.execute(current_user.id)
    return TwoFactorSetupResponse(secret=result.secret, qr_code_base64=result.qr_code_base64)


@router.post("/confirm-2fa", response_model=MessageResponse)
async def confirm_2fa(
    code: str,
    current_user: UserDomain = Depends(get_current_user),
    uc: Confirm2FAUseCase = Depends(get_confirm_2fa_uc),
):
    await uc.execute(current_user.id, code)
    return MessageResponse(message="2FA has been enabled successfully")


@router.post("/disable-2fa", response_model=MessageResponse)
async def disable_2fa(
    code: str,
    current_user: UserDomain = Depends(get_current_user),
    uc: Disable2FAUseCase = Depends(get_disable_2fa_uc),
):
    await uc.execute(current_user.id, code)
    return MessageResponse(message="2FA has been disabled successfully")


@router.post("/verify-2fa", response_model=TokenResponse)
async def verify_2fa(
    request: Request,
    data: Verify2FARequest,
    uc: Verify2FAAndLoginUseCase = Depends(get_verify_2fa_uc),
    _rl=Depends(make_rate_limiter(limit=5, window=60)),
):
    device_info = f"{request.headers.get('user-agent', 'unknown')} - {request.client.host}"
    return _token_response(await uc.execute(data.temp_token, data.code, device_info))


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: UserDomain = Depends(get_current_user)):
    return UserMeResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
        is_verified=current_user.is_verified,
        is_2fa_enabled=current_user.is_2fa_enabled,
        oauth_provider=current_user.oauth_provider,
    )
