from src.core_context.user.application.queries import GetMyProfileQuery
from src.core_context.user.application.read_models import FullProfileReadModel
from src.core_context.user.domain.errors import UserNotFoundError
from src.core_context.user.infrastructure.read_repository import SqlAlchemyUserProfileReadRepository


class GetMyProfileQueryHandler:
    def __init__(self, read_repo: SqlAlchemyUserProfileReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: GetMyProfileQuery) -> FullProfileReadModel:
        profile = await self._read_repo.get_full_profile(query.user_id)
        if not profile:
            raise UserNotFoundError(query.user_id)
        return profile
