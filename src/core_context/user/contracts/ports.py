from typing import Protocol, runtime_checkable

from src.core_context.user.contracts.dtos import UserProfileDTO


@runtime_checkable
class IUserProfileDirectory(Protocol):
    async def get_profile(self, user_id: int) -> UserProfileDTO | None: ...
