
from sqlalchemy import select, update
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
    async def create(db: AsyncSession, name: str, email: str, password_hash: str) -> User:
        new_user = User(name=name, email=email, password_hash=password_hash)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    
    @staticmethod
    async def mark_as_verified(db: AsyncSession, user_id: int) -> None:
        stmt = update(User).where(User.id == user_id).values(is_verified=True)
        await db.execute(stmt)
        await db.commit() 