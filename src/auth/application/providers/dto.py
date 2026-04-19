from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    provider: str
    provider_id: str
    email: str
    name: str
    avatar_url: str | None = None
    is_verified: bool = False
