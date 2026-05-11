
from src.gamification.application.queries import GetGamificationProfileQuery
from src.gamification.domain.interfaces import IGamificationRepository
from src.models.gamification import GamificationProfile


class GetGamificationProfileQueryHandler:
    def __init__(self, repository: IGamificationRepository) -> None:
        self._repository = repository

    async def handle(
        self, query: GetGamificationProfileQuery
    ) -> GamificationProfile | None:
        return await self._repository.get_by_user_id(query.user_id)