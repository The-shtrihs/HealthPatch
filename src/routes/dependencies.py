from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.repositories.user import UserRepository
from src.services.auth import AuthService

ouath2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(ouath2_scheme), db: AsyncSession = Depends(get_session)):
    try:
        payload = AuthService.decode_access_token(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={"WWW-Authenticate": "Bearer"})
    user_id = int(payload.get("sub"))
    current_user = await UserRepository.get_by_id(db, user_id)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return current_user

async def get_auth_service(db: AsyncSession = Depends(get_session)):
    return AuthService(db)


