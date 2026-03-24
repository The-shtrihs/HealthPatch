import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import BackgroundTasks

from src.core.config import get_settings
from src.core.exceptions import (
    EmailAlreadyExistsError,
    EmailAlreadyVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidTwoFactorCodeError,
    NotFoundError,
    PasswordMismatchError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
    UserInactiveError,
)
from src.models.user import RefreshToken, User
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.user import UserRepository
from src.schemas.auth import ChangePasswordRequest, MessageResponse, TokenResponse, TwoFactorSetupResponse
from src.services.mail import MailService
from src.services.totp import TotpService


class AuthService:
    def __init__(self, user_repo: UserRepository, token_repo: RefreshTokenRepository, mail_service: MailService, totp_service: TotpService):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.mail_service = mail_service
        self.totp_service = totp_service
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
        expire = datetime.now(UTC) + timedelta(minutes=self.settings.access_token_expire_minutes)
        payload = {"sub": str(user.id), "email": user.email, "type": "access", "iat": datetime.now(UTC), "exp": expire}
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.settings.algorithm)

    async def create_refresh_token(self, user: User, device_info: str | None = None) -> str:
        token_value = secrets.token_urlsafe(64)
        expires_at = datetime.now(UTC) + timedelta(minutes=self.settings.refresh_token_expire_minutes)
        await self.token_repo.create(token_value, user.id, expires_at, device_info)
        return token_value

    def create_2fa_token(self, user: User) -> str:
        expire = datetime.now(UTC) + timedelta(minutes=5)
        payload = {"sub": str(user.id), "email": user.email, "type": "2fa", "iat": datetime.now(UTC), "exp": expire}
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.settings.algorithm)

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

    @staticmethod
    def decode_2fa_token(token: str) -> dict:
        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            if payload.get("type") != "2fa":
                raise InvalidTokenError("Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("2FA token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid 2FA token: {str(e)}")

    async def verify_refresh_token(self, token: str) -> RefreshToken:
        db_token = await self.token_repo.get_active_token(token)
        if not db_token:
            raise InvalidTokenError("Invalid refresh token")

        if db_token.expires_at < datetime.now(UTC):
            await self.token_repo.mark_as_revoked(db_token)
            raise InvalidTokenError("Refresh token has expired")

        return db_token

    async def revoke_refresh_token(self, token: str):
        db_token = await self.token_repo.get_active_token(token)
        if db_token:
            await self.token_repo.mark_as_revoked(db_token)

    async def revoke_all_refresh_tokens_for_user(self, user_id: int):
        await self.token_repo.revoke_all_for_user(user_id)

    async def register_user(self, name: str, email: str, password: str, background_tasks: BackgroundTasks) -> None:
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise EmailAlreadyExistsError()

        password_hash = self.hash_password(password)
        user = await self.user_repo.create(name=name, email=email, password_hash=password_hash)
        background_tasks.add_task(self.mail_service.send_verification_email, user_id=user.id, user_email=email, name=name)

    async def authenticate_user(self, email: str, password: str, device_info: str | None = None) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)

        if not user:
            raise InvalidCredentialsError()

        if not user.password_hash:
            raise InvalidCredentialsError(message="This email is registered with an OAuth provider. Please log in using that provider.")

        if not self.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise UserInactiveError()

        if user.is_2fa_enabled:
            temp_token = self.create_2fa_token(user)
            return TokenResponse(
                access_token=temp_token,
                refresh_token=None,
                token_type="2fa_required",
                expires_in=5 * 60,
            )

        access_token = self.create_access_token(user)
        refresh_token = await self.create_refresh_token(user, device_info=device_info)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        db_token = await self.verify_refresh_token(refresh_token)
        user = await self.user_repo.get_by_id(db_token.user_id)

        if not user or not user.is_active:
            raise UserInactiveError()

        access_token = self.create_access_token(user)
        new_refresh_token = await self.create_refresh_token(user, device_info=None)

        await self.token_repo.mark_as_revoked(db_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )

    async def logout(self, refresh_token: str):
        await self.revoke_refresh_token(refresh_token)

    async def logout_all_sessions(self, user_id: int):
        await self.revoke_all_refresh_tokens_for_user(user_id)

    async def change_password(self, change_password_request: ChangePasswordRequest, user_id: int):
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)

        if not self.verify_password(change_password_request.current_password, user.password_hash):
            raise PasswordMismatchError()

        new_password_hash = self.hash_password(change_password_request.new_password)
        await self.user_repo.update_password(user_id, new_password_hash)
        await self.revoke_all_refresh_tokens_for_user(user_id)

    async def forgot_password(self, email: str, background_tasks: BackgroundTasks):
        user = await self.user_repo.get_by_email(email)
        if user:
            background_tasks.add_task(self.mail_service.send_password_reset_email, user_id=user.id, user_email=email, name=user.name)

    async def resend_verification_email(self, email: str, background_tasks: BackgroundTasks):
        user = await self.user_repo.get_by_email(email)
        if user and not user.is_verified:
            background_tasks.add_task(self.mail_service.send_verification_email, user_id=user.id, user_email=email, name=user.name)

    async def verify_email(self, token: str):
        payload = self.mail_service.decode_email_token(token, expected_purpose="email_verify")
        user_id = int(payload.get("sub"))
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)
        if user.is_verified:
            raise EmailAlreadyVerifiedError()

        await self.user_repo.mark_as_verified(user_id)

    async def reset_password(self, token: str, change_password_request: ChangePasswordRequest):
        payload = self.mail_service.decode_email_token(token, expected_purpose="password_reset")
        user_id = int(payload.get("sub"))
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)

        new_password_hash = self.hash_password(change_password_request.new_password)
        await self.user_repo.update_password(user_id, new_password_hash)
        await self.revoke_all_refresh_tokens_for_user(user_id)

    async def enable_2fa(self, user_id: int) -> TwoFactorSetupResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)

        if user.is_2fa_enabled:
            raise TwoFactorAlreadyEnabledError()

        secret = self.totp_service.generate_totp_secret()
        uri = self.totp_service.get_totp_uri(secret, user_email=user.email)
        qr_code_base64 = self.totp_service.generate_qr_code_base64(uri)
        await self.user_repo.update_totp_secret(user_id, secret)
        return TwoFactorSetupResponse(secret=secret, qr_code_base64=qr_code_base64)

    async def confirm_2fa_setup(self, user_id: int, code: str) -> MessageResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)

        if not user.totp_secret:
            raise TwoFactorNotEnabledError("Cannot confirm 2FA setup because it was not initiated")

        if not self.totp_service.verify_totp(code, user.totp_secret):
            raise InvalidTwoFactorCodeError()

        await self.user_repo.update_2fa_enabled(user_id, True)
        return MessageResponse(message="2FA has been enabled successfully")

    async def disable_2fa(self, user_id: int, code: str) -> MessageResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)

        if not user.is_2fa_enabled or not user.totp_secret:
            raise TwoFactorNotEnabledError()

        if not self.totp_service.verify_totp(code, user.totp_secret):
            raise InvalidTwoFactorCodeError()

        await self.user_repo.update_2fa_enabled(user_id, False)
        await self.user_repo.update_totp_secret(user_id, None)
        return MessageResponse(message="2FA has been disabled successfully")

    async def verify_2fa_token(self, temp_token: str, code: str, device_info: str = None) -> TokenResponse:
        payload = self.decode_2fa_token(temp_token)
        user_id = int(payload.get("sub"))
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError(resource="User", resource_id=user_id)

        if not user.is_2fa_enabled or not user.totp_secret:
            raise TwoFactorNotEnabledError()

        if not self.totp_service.verify_totp(code, user.totp_secret):
            raise InvalidTwoFactorCodeError()

        access_token = self.create_access_token(user)
        refresh_token = await self.create_refresh_token(user, device_info=device_info)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )
