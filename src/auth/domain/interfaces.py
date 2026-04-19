from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol

from src.auth.domain.models import OAuthStateData, RefreshTokenDomain, UserDomain


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> UserDomain | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> UserDomain | None: ...

    @abstractmethod
    async def get_by_oauth(self, provider: str, provider_id: str) -> UserDomain | None: ...

    @abstractmethod
    async def create(
        self,
        name: str,
        email: str,
        password_hash: str | None,
        provider: str | None = None,
        provider_id: str | None = None,
        avatar_url: str | None = None,
    ) -> UserDomain: ...

    @abstractmethod
    async def save(self, user: UserDomain) -> UserDomain: ...


class IRefreshTokenRepository(ABC):
    @abstractmethod
    async def create(self, token: str, user_id: int, expires_at: datetime, device_info: str | None) -> RefreshTokenDomain: ...

    @abstractmethod
    async def get_active_token(self, token: str) -> RefreshTokenDomain | None: ...

    @abstractmethod
    async def save(self, token: RefreshTokenDomain) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: int) -> None: ...


class IOAuthStateRepository(ABC):
    @abstractmethod
    async def create(
        self,
        provider: str,
        redirect_after: str = "/",
        ip_address: str | None = None,
    ) -> str: ...

    @abstractmethod
    async def validate_and_consume(self, state: str) -> OAuthStateData | None: ...


class IMailService(Protocol):
    async def send_verification_email(self, user_id: int, user_email: str, name: str) -> None: ...
    async def send_password_reset_email(self, user_id: int, user_email: str, name: str) -> None: ...
    def decode_email_token(self, token: str, expected_purpose: str) -> dict: ...


class ITotpService(Protocol):
    def generate_totp_secret(self) -> str: ...
    def get_totp_uri(self, secret: str, user_email: str) -> str: ...
    def generate_qr_code_base64(self, uri: str) -> str: ...
    def verify_totp(self, code: str, secret: str) -> bool: ...
