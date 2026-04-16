from src.auth.domain.models import RefreshTokenDomain, UserDomain
from src.models.user import RefreshToken, User  


def user_orm_to_domain(orm: User) -> UserDomain:
    return UserDomain(
        id=orm.id,
        name=orm.name,
        email=orm.email,
        password_hash=orm.password_hash,
        is_verified=orm.is_verified,
        is_active=orm.is_active,
        oauth_provider=orm.oauth_provider,
        oauth_provider_id=orm.oauth_provider_id,
        avatar_url=orm.avatar_url,
        totp_secret=orm.totp_secret,
        is_2fa_enabled=orm.is_2fa_enabled,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def refresh_token_orm_to_domain(orm: RefreshToken) -> RefreshTokenDomain:
    return RefreshTokenDomain(
        id=orm.id,
        token=orm.token,
        user_id=orm.user_id,
        expires_at=orm.expires_at,
        is_revoked=orm.is_revoked,
        device_info=orm.device_info,
        created_at=orm.created_at,
    )


def apply_domain_to_user_orm(domain: UserDomain, orm: User) -> None:
    orm.name = domain.name
    orm.email = domain.email
    orm.password_hash = domain.password_hash
    orm.is_verified = domain.is_verified
    orm.is_active = domain.is_active
    orm.oauth_provider = domain.oauth_provider
    orm.oauth_provider_id = domain.oauth_provider_id
    orm.avatar_url = domain.avatar_url
    orm.totp_secret = domain.totp_secret
    orm.is_2fa_enabled = domain.is_2fa_enabled