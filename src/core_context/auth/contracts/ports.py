from typing import Protocol, runtime_checkable

from src.core_context.auth.contracts.dtos import UserSummaryDTO


@runtime_checkable
class IUserDirectory(Protocol):
    async def get_user(self, user_id: int) -> UserSummaryDTO | None: ...
