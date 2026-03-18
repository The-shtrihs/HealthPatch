

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.models.user import User
from src.routes.dependencies import get_auth_service, get_current_user
from src.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, MessageResponse, RegisterRequest, RegisterResponse
from src.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201, response_model=RegisterResponse)
async def register(data: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        await auth_service.register_user(data.name, data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="User registered successfully")


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        auth_data = await auth_service.authenticate_user(data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return auth_data

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(refresh_token: str, auth_service: AuthService = Depends(get_auth_service)):
    try:
        auth_data = await auth_service.refresh_access_token(refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return auth_data

@router.post("/logout", status_code=204)
async def logout(refresh_token: str, auth_service: AuthService = Depends(get_auth_service)):
    await auth_service.logout(refresh_token)
    return MessageResponse(message="Logged out successfully")

@router.post("/logout-all", status_code=204)
async def logout_all(auth_service: AuthService = Depends(get_auth_service), current_user: User = Depends(get_current_user)):
    await auth_service.logout_all_sessions(current_user.id)
    return MessageResponse(message="Logged out from all sessions successfully")

@router.post("/change-password", status_code=204)
async def change_password(change_password_request: ChangePasswordRequest, user_id: int, auth_service: AuthService = Depends(get_auth_service)):
    try:
        await auth_service.change_password(change_password_request, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Password changed successfully")

@router.post("/forgot-password", status_code=204)
async def forgot_password(email: str, background_tasks: BackgroundTasks, auth_service: AuthService = Depends(get_auth_service)):
    await auth_service.forgot_password(email, background_tasks)
    return MessageResponse(message="If an account with that email exists, a password reset link has been sent")

@router.post("/resend-verification-email", status_code=204)
async def resend_verification_email(email: str, background_tasks: BackgroundTasks, auth_service: AuthService = Depends(get_auth_service)):
    await auth_service.resend_verification_email(email, background_tasks)
    return MessageResponse(message="If an account with that email exists and is not verified, a verification email has been resent")