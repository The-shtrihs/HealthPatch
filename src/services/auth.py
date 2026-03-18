import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.exceptions import (
    EmailAlreadyExistsError,
    EmailAlreadyVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
    UserInactiveError,
)
from src.models.user import RefreshToken, User
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.user import UserRepository
from src.schemas.auth import ChangePasswordRequest, LoginResponse
from src.services.mail import MailService


class AuthService:
    def __init__(self, db: AsyncSession, mail_service: MailService):
        self.db = db
        self.settings = get_settings()
        self.ph = PasswordHasher()
        self.mail_service = mail_service

    def hash_password(self, password: str) -> str:
        return self.ph.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self.ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False

    def create_access_token(self, user: User) -> str:
        expire = datetime.now(UTC) + timedelta(minutes=self.settings.access_token_expire_minutes)
        payload = {"sub": str(user.id), "email": user.email, "type": "access", "iat": datetime.now(UTC), "exp": expire}
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.settings.algorithm)

    async def create_refresh_token(self, user: User, device_info: str | None = None) -> str:
        token_value = secrets.token_urlsafe(64)
        expires_at = datetime.now(UTC) + timedelta(minutes=self.settings.refresh_token_expire_minutes)
        await RefreshTokenRepository.create(self.db, token_value, user.id, expires_at, device_info)
        return token_value

    @staticmethod
    def decode_access_token(token: str) -> dict:
        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            if payload.get("type") != "access":
                raise InvalidTokenError("Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")

    async def verify_refresh_token(self, token: str) -> RefreshToken:
        db_token = await RefreshTokenRepository.get_active_token(self.db, token)
        if not db_token:
            raise InvalidTokenError("Invalid refresh token")

        if db_token.expires_at < datetime.now(UTC):
            await RefreshTokenRepository.mark_as_revoked(self.db, db_token)
            raise InvalidTokenError("Refresh token has expired")

        return db_token

    async def revoke_refresh_token(self, token: str):
        db_token = await RefreshTokenRepository.get_active_token(self.db, token)
        if db_token:
            await RefreshTokenRepository.mark_as_revoked(self.db, db_token)

    async def revoke_all_refresh_tokens_for_user(self, user_id: int):
        await RefreshTokenRepository.revoke_all_for_user(self.db, user_id)

    async def register_user(self, name: str, email: str, password: str, background_tasks: BackgroundTasks) -> None:
        existing_user = await UserRepository.get_by_email(self.db, email)
        if existing_user:
            raise EmailAlreadyExistsError()

        password_hash = self.hash_password(password)
        user = await UserRepository.create(self.db, name, email, password_hash)
        background_tasks.add_task(self.mail_service.send_verification_email, user_id=user.id, user_email=email, name=name)

    async def authenticate_user(self, email: str, password: str) -> LoginResponse:
        user = await UserRepository.get_by_email(self.db, email)

        if not user or not self.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise UserInactiveError()

        access_token = self.create_access_token(user)
        refresh_token = await self.create_refresh_token(user, device_info=None)

        return LoginResponse(
            token_response={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.settings.access_token_expire_minutes * 60,
            },
            name=user.name,
            email=user.email,
        )

    async def refresh_access_token(self, refresh_token: str) -> LoginResponse:
        db_token = await self.verify_refresh_token(refresh_token)
        user = await UserRepository.get_by_id(self.db, db_token.user_id)

        if not user or not user.is_active:
            raise UserInactiveError()

        access_token = self.create_access_token(user)
        new_refresh_token = await self.create_refresh_token(user, device_info=None)

        await RefreshTokenRepository.mark_as_revoked(self.db, db_token)

        return LoginResponse(
            token_response={
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": self.settings.access_token_expire_minutes * 60,
            },
            name=user.name,
            email=user.email,
        )

    async def logout(self, refresh_token: str):
        await self.revoke_refresh_token(refresh_token)

    async def logout_all_sessions(self, user_id: int):
        await self.revoke_all_refresh_tokens_for_user(user_id)

    async def change_password(self, change_password_request: ChangePasswordRequest, user_id: int):
        user = await UserRepository.get_by_id(self.db, user_id)

        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)

        if not self.verify_password(change_password_request.current_password, user.password_hash):
            raise InvalidCredentialsError(message="Current password is incorrect")

        new_password_hash = self.hash_password(change_password_request.new_password)
        await UserRepository.update_password(self.db, user_id, new_password_hash)
        await self.revoke_all_refresh_tokens_for_user(user_id)

    async def forgot_password(self, email: str, background_tasks: BackgroundTasks):
        user = await UserRepository.get_by_email(self.db, email)
        if user:
            background_tasks.add_task(self.mail_service.send_password_reset_email, user_id=user.id, user_email=email, name=user.name)

    async def resend_verification_email(self, email: str, background_tasks: BackgroundTasks):
        user = await UserRepository.get_by_email(self.db, email)
        if user and not user.is_verified:
            background_tasks.add_task(self.mail_service.send_verification_email, user_id=user.id, user_email=email, name=user.name)

    async def verify_email(self, token: str):
        payload = self.mail_service.decode_email_token(token, expected_purpose="email_verify")
        user_id = int(payload.get("sub"))
        user = await UserRepository.get_by_id(self.db, user_id)
        
        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)
        if user.is_verified:
            raise EmailAlreadyVerifiedError()
            
        await UserRepository.mark_as_verified(self.db, user_id)

    async def reset_password(self, token: str, change_password_request: ChangePasswordRequest):
        payload = self.mail_service.decode_email_token(token, expected_purpose="password_reset")
        user_id = int(payload.get("sub"))
        user = await UserRepository.get_by_id(self.db, user_id)
        
        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)
            
        new_password_hash = self.hash_password(change_password_request.new_password)
        await UserRepository.update_password(self.db, user_id, new_password_hash)
        await self.revoke_all_refresh_tokens_for_user(user_id)