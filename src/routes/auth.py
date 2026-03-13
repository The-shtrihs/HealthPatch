

from fastapi import APIRouter, Depends, HTTPException

from src.routes.dependencies import get_auth_service
from src.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from src.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=201, response_model=RegisterResponse)
async def register(data: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        await auth_service.register_user(data.name, data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RegisterResponse(message="User registered successfully")

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        auth_data = await auth_service.authenticate_user(data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return auth_data