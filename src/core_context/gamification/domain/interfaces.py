from abc import ABC, abstractmethod


class IGamificationRepository(ABC):
    @abstractmethod
    async def ensure_profile(self, user_id: int) -> None: ...

    @abstractmethod
    async def award_xp(self, user_id: int, xp: int) -> int: ...
