from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_oauth(self, provider: str, provider_id: str) -> User | None:
        result = await self.db.scalars(select(User).where(User.oauth_provider == provider, User.oauth_provider_id == provider_id))
        return result.first()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.scalars(select(User).where(User.email == email))
        return result.first()

    async def update_password(self, user_id: int, new_password_hash: str):
        user = await self.db.get(User, user_id)
        if user:
            user.password_hash = new_password_hash
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        return None

    async def update_oauth_info(self, user: User, provider: str, provider_id: str, avatar_url: str | None = None):
        user.oauth_provider = provider
        user.oauth_provider_id = provider_id
        if avatar_url:
            user.avatar_url = avatar_url
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def create(
            self, name: str, 
            email: str, 
            password_hash: str | None, 
            provider: str | None = None, 
            provider_id: str | None = None, 
            avatar_url: str | None = None) -> User:
        new_user = User(
            name=name, email=email, password_hash=password_hash, oauth_provider=provider, oauth_provider_id=provider_id, avatar_url=avatar_url
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def mark_as_verified(self, user_id: int) -> None:
        stmt = update(User).where(User.id == user_id).values(is_verified=True)
        await self.db.execute(stmt)
        await self.db.commit()

    async def update_totp_secret(self, user_id: int, totp_secret: str | None) -> None:
        stmt = update(User).where(User.id == user_id).values(totp_secret=totp_secret)
        await self.db.execute(stmt)
        await self.db.commit()

    async def update_2fa_enabled(self, user_id: int, is_enabled: bool) -> None:
        stmt = update(User).where(User.id == user_id).values(is_2fa_enabled=is_enabled)
        await self.db.execute(stmt)
        await self.db.commit()