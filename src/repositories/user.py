from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class UserRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        return await db.get(User, user_id)

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.scalars(select(User).where(User.email == email))
        return result.first()

    @staticmethod
    async def create(db: AsyncSession, name: str, email: str, password_hash: str) -> User:
        new_user = User(name=name, email=email, password_hash=password_hash)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
