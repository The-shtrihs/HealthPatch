from dataclasses import dataclass


@dataclass(frozen=True)
class UserReadModel:
    id: int
    name: str
    email: str
    avatar_url: str | None
    is_verified: bool
    is_2fa_enabled: bool
    oauth_provider: str | None


@dataclass(frozen=True)
class TokenReadModel:
    access_token: str
    refresh_token: str | None
    token_type: str
    expires_in: int


@dataclass(frozen=True)
class TwoFactorSetupReadModel:
    secret: str
    qr_code_base64: str

@dataclass(frozen=True)
class MessageReadModel:
    message: str