from abc import ABC, abstractmethod

from src.user.domain.models import FitnessProfileDomain, UserProfileDomain


class IUserProfileRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> UserProfileDomain | None: ...

    @abstractmethod
    async def save_user_info(self, user_id: int, name: str, avatar_url: str | None) -> None: ...

    @abstractmethod
    async def save_fitness(self, user_id: int, fitness: FitnessProfileDomain) -> None: ...

    @abstractmethod
    async def deactivate(self, user_id: int) -> None: ...
