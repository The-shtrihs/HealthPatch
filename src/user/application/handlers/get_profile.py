from src.user.application.queries import GetMyProfileQuery
from src.user.application.read_models import FullProfileReadModel
from src.user.domain.errors import UserNotFoundError
from src.user.infrastructure.read_repository import SqlAlchemyUserProfileReadRepository


class GetMyProfileQueryHandler:
    def __init__(self, read_repo: SqlAlchemyUserProfileReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: GetMyProfileQuery) -> FullProfileReadModel:
        profile = await self._read_repo.get_full_profile(query.user_id)
        if not profile:
            raise UserNotFoundError(query.user_id)
        return profile
