from abc import ABC, abstractmethod

from src.models.gamification import GamificationProfile


class IGamificationRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> GamificationProfile | None: ...

    @abstractmethod
    async def add(self, profile: GamificationProfile) -> None: ...
