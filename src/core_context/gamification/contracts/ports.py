from typing import Protocol, runtime_checkable

from src.core_context.gamification.contracts.dtos import GamificationProfileDTO


@runtime_checkable
class IGamificationDirectory(Protocol):
    async def get_profile(self, user_id: int) -> GamificationProfileDTO | None: ...
