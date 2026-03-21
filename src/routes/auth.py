from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.models.user import User
from src.routes.dependencies import get_auth_service, get_current_user
from src.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    TwoFactorSetupResponse,
    UserProfileResponse,
    Verify2FARequest,
)
from src.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201, response_model=RegisterResponse)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.register_user(data.name, data.email, data.password, background_tasks)
    return MessageResponse(message="User registered successfully. Please check your email to verify your account.")


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    device_info = f"{request.headers.get('user-agent', 'unknown')} - {request.client.host}"
    auth_data = await auth_service.authenticate_user(data.email, data.password, device_info=device_info)
    return auth_data


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, auth_service: AuthService = Depends(get_auth_service)):
    auth_data = await auth_service.refresh_access_token(refresh_token)
    return auth_data


@router.post("/logout", response_model=MessageResponse)
async def logout(refresh_token: str, auth_service: AuthService = Depends(get_auth_service)):
    await auth_service.logout(refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    await auth_service.logout_all_sessions(current_user.id)
    return MessageResponse(message="Logged out from all sessions successfully")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    change_password_request: ChangePasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    await auth_service.change_password(change_password_request, current_user.id)
    return MessageResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.forgot_password(email, background_tasks)
    return MessageResponse(message="If an account with that email exists, a password reset link has been sent")


@router.post("/resend-verification-email", response_model=MessageResponse)
async def resend_verification_email(
    email: str,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.resend_verification_email(email, background_tasks)
    return MessageResponse(message="If an account with that email exists and is not verified, a verification email has been resent")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(token: str, auth_service: AuthService = Depends(get_auth_service)):
    await auth_service.verify_email(token)
    return MessageResponse(message="Email verified successfully")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    token: str,
    change_password_request: ChangePasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.reset_password(token, change_password_request)
    return MessageResponse(message="Password reset successfully")


@router.post("/enable-2fa", response_model=TwoFactorSetupResponse)
async def enable_2fa(
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    return await auth_service.enable_2fa(current_user.id)
    

@router.post("/confirm-2fa", response_model=MessageResponse)
async def confirm_2fa(
    code: str,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    return await auth_service.confirm_2fa_setup(current_user.id, code)

@router.post("/disable-2fa", response_model=MessageResponse)
async def disable_2fa(
    code: str,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    return await auth_service.disable_2fa(current_user.id, code)


@router.post("/verify-2fa", response_model=TokenResponse)
async def verify_2fa(
    request: Request,
    data: Verify2FARequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    device_info = f"{request.headers.get('user-agent', 'unknown')} - {request.client.host}"
    return await auth_service.verify_2fa_token(data.temp_token, data.code, device_info)


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
