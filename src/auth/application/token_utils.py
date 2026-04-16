from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from src.auth.domain.errors import InvalidTokenError
from src.core.config import get_settings
from src.core.constants import TWO_FA_TOKEN_EXPIRE_MINUTES
import secrets
from datetime import UTC, datetime, timedelta

from src.auth.domain.interfaces import IRefreshTokenRepository
from src.auth.domain.models import RefreshTokenDomain
from src.core.config import get_settings
from src.core.constants import REFRESH_TOKEN_BYTES

async def issue_refresh_token(
    token_repo: IRefreshTokenRepository,
    user_id: int,
    device_info: str | None = None,
) -> str:
    settings = get_settings()
    token_value = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.refresh_token_expire_minutes)
    await token_repo.create(token_value, user_id, expires_at, device_info)
    return token_value


class PasswordUtils:
    def __init__(self):
        self._ph = PasswordHasher()

    def hash(self, password: str) -> str:
        return self._ph.hash(password)

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return self._ph.verify(hashed, plain)
        except VerifyMismatchError:
            return False


class TokenUtils:

    @staticmethod
    def create_access_token(user_id: int, email: str) -> str:
        settings = get_settings()
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "access",
            "iat": datetime.now(UTC),
            "exp": expire,
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def create_2fa_token(user_id: int, email: str) -> str:
        settings = get_settings()
        expire = datetime.now(UTC) + timedelta(minutes=TWO_FA_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "2fa",
            "iat": datetime.now(UTC),
            "exp": expire,
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

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
            raise InvalidTokenError(f"Invalid token: {e}")

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
            raise InvalidTokenError(f"Invalid 2FA token: {e}")
        
    