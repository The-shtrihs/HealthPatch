from abc import ABC, abstractmethod
from datetime import date


class IGamificationRepository(ABC):
    @abstractmethod
    async def ensure_profile(self, user_id: int) -> None: ...

    @abstractmethod
    async def award_xp(self, user_id: int, xp: int) -> int: ...

    @abstractmethod
    async def count_meal_entries_for_day(self, user_id: int, target_date: date) -> int: ...
