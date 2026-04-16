from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.domain.interfaces import IRefreshTokenRepository, IUserRepository
from src.auth.domain.models import RefreshTokenDomain, UserDomain
from src.auth.infrastructure.mapper import (
    apply_domain_to_user_orm, refresh_token_orm_to_domain, user_orm_to_domain,
)
from src.models.user import RefreshToken, User


class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, user_id: int) -> UserDomain | None:
        orm = await self._db.get(User, user_id)
        return user_orm_to_domain(orm) if orm else None

    async def get_by_email(self, email: str) -> UserDomain | None:
        result = await self._db.scalars(select(User).where(User.email == email))
        orm = result.first()
        return user_orm_to_domain(orm) if orm else None

    async def get_by_oauth(self, provider: str, provider_id: str) -> UserDomain | None:
        result = await self._db.scalars(
            select(User).where(
                User.oauth_provider == provider,
                User.oauth_provider_id == provider_id,
            )
        )
        orm = result.first()
        return user_orm_to_domain(orm) if orm else None

    async def create(
        self, name: str, email: str, password_hash: str | None,
        provider: str | None = None, provider_id: str | None = None,
        avatar_url: str | None = None,
    ) -> UserDomain:
        orm = User(
            name=name, email=email, password_hash=password_hash,
            oauth_provider=provider, oauth_provider_id=provider_id,
            avatar_url=avatar_url,
        )
        self._db.add(orm)
        await self._db.commit()
        await self._db.refresh(orm)
        return user_orm_to_domain(orm)

    async def save(self, user: UserDomain) -> UserDomain:
        orm = await self._db.get(User, user.id)
        apply_domain_to_user_orm(user, orm)
        self._db.add(orm)
        await self._db.commit()
        await self._db.refresh(orm)
        return user_orm_to_domain(orm)


class SqlAlchemyRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self, token: str, user_id: int,
        expires_at: datetime, device_info: str | None,
    ) -> RefreshTokenDomain:
        orm = RefreshToken(
            token=token, user_id=user_id,
            expires_at=expires_at, device_info=device_info,
        )
        self._db.add(orm)
        await self._db.commit()
        await self._db.refresh(orm)
        return refresh_token_orm_to_domain(orm)

    async def get_active_token(self, token: str) -> RefreshTokenDomain | None:
        result = await self._db.scalars(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.is_revoked.is_(False),
            )
        )
        orm = result.first()
        return refresh_token_orm_to_domain(orm) if orm else None

    async def save(self, token: RefreshTokenDomain) -> None:
        await self._db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token.id)
            .values(is_revoked=token.is_revoked)
        )
        await self._db.commit()

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self._db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        await self._db.commit()