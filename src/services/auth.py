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
from src.schemas.auth import LoginResponse


class AuthService:
    def __init__(self, db: AsyncSession):

        self.db = db
        self.settings = get_settings()
        self.ph = PasswordHasher()

    def hash_password(self, password: str) -> str:
        return self.ph.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self.ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False
        
    def create_access_token(self, user: User) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.access_token_expire_minutes)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": expire
        }
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.settings.algorithm)

    async def create_refresh_token(self, user: User, device_info: str | None = None) -> str:
        token_value = secrets.token_urlsafe(64)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.settings.refresh_token_expire_minutes)
        await RefreshTokenRepository.create(self.db, token_value, user.id, expires_at, device_info)
        return token_value
    
    @staticmethod
    def decode_access_token(token: str) -> dict:
        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            if payload.get("type") != "access":
                raise jwt.InvalidTokenError("Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError as e:
            raise Exception(f"Invalid token: {str(e)}")

    async def verify_refresh_token(self, token: str) -> RefreshToken:
        db_token = await RefreshTokenRepository.get_active_token(self.db, token)
        if not db_token:
            raise ValueError("Invalid refresh token")
            
        if db_token.expires_at < datetime.now(timezone.utc):
            await RefreshTokenRepository.mark_as_revoked(self.db, db_token)
            raise ValueError("Refresh token has expired")
            
        return db_token

    async def revoke_refresh_token(self, token: str):
        db_token = await RefreshTokenRepository.get_active_token(self.db, token)
        if db_token:
            await RefreshTokenRepository.mark_as_revoked(self.db, db_token)

    async def revoke_all_refresh_tokens_for_user(self, user_id: int):
        await RefreshTokenRepository.revoke_all_for_user(self.db, user_id)


    async def register_user(self, name: str, email: str, password: str) -> None:
        existing_user = await UserRepository.get_by_email(self.db, email)
        if existing_user:
            raise ValueError("Email already registered")
        
        password_hash = self.hash_password(password)
        await UserRepository.create(self.db, name, email, password_hash)
      

    async def authenticate_user(self, email: str, password: str) -> LoginResponse:
        user = await UserRepository.get_by_email(self.db, email)
        
        if not user or not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
            
        if not user.is_active:
            raise ValueError("User account is inactive")
            
        access_token = self.create_access_token(user)
        refresh_token = await self.create_refresh_token(user, device_info=None)

        return LoginResponse(
            token_response={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.settings.access_token_expire_minutes * 60
            },
            name=user.name,
            email=user.email
        )