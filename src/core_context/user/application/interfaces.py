from abc import ABC, abstractmethod

from src.core_context.user.application.read_models import FullProfileReadModel


class IUserProfileReadRepository(ABC):
    @abstractmethod
    async def get_full_profile(self, user_id: int) -> FullProfileReadModel | None: ...
