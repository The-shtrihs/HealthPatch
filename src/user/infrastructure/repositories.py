from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User, UserProfile
from src.user.domain.interfaces import IUserProfileRepository
from src.user.domain.models import FitnessGoal, FitnessProfileDomain, Gender, UserProfileDomain

from src.user.infrastructure.mapper import _orm_to_fitness, _orm_to_profile

class SqlAlchemyUserProfileRepository(IUserProfileRepository):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_full_profile(self, user_id: int) -> UserProfileDomain | None:
        result = await self._db.scalars(
            select(User).where(User.id == user_id).options(selectinload(User.profile))
        )
        user = result.first()
        return _orm_to_profile(user) if user else None

    async def save_user_info(self, user_id: int, name: str, avatar_url: str | None) -> UserProfileDomain:
        user = await self._db.get(User, user_id)
        user.name = name
        user.avatar_url = avatar_url
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return await self.get_full_profile(user_id)

    async def save_fitness(self, user_id: int, fitness: FitnessProfileDomain) -> FitnessProfileDomain:
        result = await self._db.scalars(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            self._db.add(profile)

        profile.weight = fitness.weight
        profile.height = fitness.height
        profile.age = fitness.age
        profile.gender = fitness.gender
        profile.fitness_goal = fitness.fitness_goal

        self._db.add(profile)
        await self._db.commit()
        await self._db.refresh(profile)
        return _orm_to_fitness(profile)

    async def deactivate(self, user_id: int) -> None:
        user = await self._db.get(User, user_id)
        if user:
            user.is_active = False
            self._db.add(user)
            await self._db.commit()