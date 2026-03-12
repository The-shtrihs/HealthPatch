import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models.user import RefreshToken, User
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.user import UserRepository

settings = get_settings()
ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False

def create_access_token(user: User ):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": expire
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

async def create_refresh_token(user: User, db: AsyncSession, device_info:str | None) -> str :
    token_value = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes)
    await RefreshTokenRepository.create(db, token_value, user.id, expires_at, device_info)
    return token_value

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError as e:
        raise Exception(f"Invalid token: {str(e)}")
    

async def verify_refresh_token(token: str, db: AsyncSession) -> RefreshToken:
    db_token = await RefreshTokenRepository.get_active_token(db, token)
    if not db_token:
        raise ValueError("Invalid refresh token")
    if db_token.expires_at < datetime.now(timezone.utc):
        await RefreshTokenRepository.mark_as_revoked(db, db_token)
        raise ValueError("Refresh token has expired")
    return db_token

async def revoke_refresh_token(token: str, db: AsyncSession):
    db_token = await RefreshTokenRepository.get_active_token(db, token)
    if db_token:
        await RefreshTokenRepository.mark_as_revoked(db, db_token)

async def revoke_all_refresh_tokens_for_user(user_id: int, db: AsyncSession):
    await RefreshTokenRepository.revoke_all_for_user(db, user_id)


async def register_user(db: AsyncSession, name: str, email: str, password: str) -> User:
    existing_user = await UserRepository.get_by_email(db, email)
    if existing_user:
        raise ValueError("Email already registered")
    
    password_hash = hash_password(password)
    new_user = await UserRepository.create(db, name, email, password_hash)
    return new_user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await UserRepository.get_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    if not user.is_active:
        raise ValueError("User account is inactive")
    access_token = create_access_token(user)
    refresh_token = await create_refresh_token(user, db, device_info=None)

    return {
        "token_response": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        },
        "name": user.name,
        "email": user.email
    }




