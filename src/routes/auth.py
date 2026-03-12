

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import get_session
from src.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from src.services.auth import authenticate_user, register_user

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=201, response_model=RegisterResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_session)):
    try:
        await register_user(db, data.name, data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RegisterResponse(message="User registered successfully")

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_session)):
    try:
        auth_data = await authenticate_user(db, data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return LoginResponse(**auth_data)