from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class UserRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        return await db.get(User, user_id)

    @staticmethod
    async def get_by_oauth(db: AsyncSession, provider: str, provider_id: str) -> User | None:
        result = await db.scalars(select(User).where(User.oauth_provider == provider, User.oauth_provider_id == provider_id))
        return result.first()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.scalars(select(User).where(User.email == email))
        return result.first()

    @staticmethod
    async def update_password(db: AsyncSession, user_id: int, new_password_hash: str):
        user = await db.get(User, user_id)
        if user:
            user.password_hash = new_password_hash
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        return None

    @staticmethod
    async def update_oauth_info(db: AsyncSession, user: User, provider: str, provider_id: str, avatar_url: str | None = None):
        user.oauth_provider = provider
        user.oauth_provider_id = provider_id
        if avatar_url:
            user.avatar_url = avatar_url
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        email: str,
        password_hash: str,
        provider: str | None = None,
        provider_id: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        new_user = User(
            name=name, email=email, password_hash=password_hash, oauth_provider=provider, oauth_provider_id=provider_id, avatar_url=avatar_url
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def mark_as_verified(db: AsyncSession, user_id: int) -> None:
        stmt = update(User).where(User.id == user_id).values(is_verified=True)
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def update_totp_secret(db: AsyncSession, user_id: int, totp_secret: str) -> None:
        stmt = update(User).where(User.id == user_id).values(totp_secret=totp_secret)
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def update_2fa_enabled(db: AsyncSession, user_id: int, is_enabled: bool) -> None:
        stmt = update(User).where(User.id == user_id).values(is_2fa_enabled=is_enabled)
        await db.execute(stmt)
        await db.commit()
