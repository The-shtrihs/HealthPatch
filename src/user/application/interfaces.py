from abc import abstractmethod, ABC

from src.user.application.read_models import FullProfileReadModel




class IUserProfileReadRepository(ABC):
    @abstractmethod
    async def get_full_profile(self, user_id: int) -> FullProfileReadModel | None: ...
        
