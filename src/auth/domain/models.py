from dataclasses import dataclass
from datetime import datetime

from src.auth.domain.errors import (
    EmailAlreadyVerifiedError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
)


@dataclass
class UserDomain:
    id: int | None
    name: str
    email: str
    password_hash: str | None
    is_verified: bool
    is_active: bool
    oauth_provider: str | None
    oauth_provider_id: str | None
    avatar_url: str | None
    totp_secret: str | None
    is_2fa_enabled: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def verify_email(self) -> None:
        if self.is_verified:
            raise EmailAlreadyVerifiedError()
        self.is_verified = True

    def initiate_2fa(self, secret: str) -> None:
        if self.is_2fa_enabled:
            raise TwoFactorAlreadyEnabledError()
        self.totp_secret = secret

    def confirm_2fa(self) -> None:
        self.is_2fa_enabled = True

    def disable_2fa(self) -> None:
        if not self.is_2fa_enabled or not self.totp_secret:
            raise TwoFactorNotEnabledError()
        self.is_2fa_enabled = False
        self.totp_secret = None

    def change_password(self, new_hash: str) -> None:
        self.password_hash = new_hash

    def deactivate(self) -> None:
        self.is_active = False


@dataclass
class RefreshTokenDomain:
    id: int | None
    token: str
    user_id: int
    expires_at: datetime
    is_revoked: bool
    device_info: str | None
    created_at: datetime | None = None

    def revoke(self) -> None:
        self.is_revoked = True

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at < now


@dataclass
class OAuthStateData:
    provider: str
    redirect_after: str
    created_at: str
    ip_address: str | None = None
