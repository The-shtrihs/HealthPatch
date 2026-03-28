from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User, UserProfile


class ProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_full_user(self, user_id: int) -> User | None:
        result = await self.db.scalars(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.profile))
        )
        return result.first()

    async def get_or_create_profile(self, user_id: int) -> UserProfile:
        result = await self.db.scalars(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
        return profile

    async def update_fitness_profile(
        self,
        user_id: int,
        weight: float | None,
        height: float | None,
        age: int | None,
        gender,
        fitness_goal,
    ) -> UserProfile:
        profile = await self.get_or_create_profile(user_id)
        if weight is not None:
            profile.weight = weight
        if height is not None:
            profile.height = height
        if age is not None:
            profile.age = age
        if gender is not None:
            profile.gender = gender
        if fitness_goal is not None:
            profile.fitness_goal = fitness_goal
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_user_info(self, user: User, name: str | None, avatar_url: str | None) -> User:
        if name is not None:
            user.name = name
        if avatar_url is not None:
            user.avatar_url = avatar_url
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def deactivate_user(self, user: User) -> None:
        user.is_active = False
        self.db.add(user)
        await self.db.commit()