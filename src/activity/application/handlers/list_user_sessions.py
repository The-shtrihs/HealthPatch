from src.activity.application.queries import ListUserSessionsQuery
from src.activity.application.read_models import PageReadModel, WorkoutSessionSummaryReadModel
from src.activity.infrastructure.read_repository import SqlAlchemyActivityReadRepository


class ListUserSessionsQueryHandler:
    def __init__(self, read_repo: SqlAlchemyActivityReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: ListUserSessionsQuery) -> PageReadModel[WorkoutSessionSummaryReadModel]:
        offset = (query.page - 1) * query.size
        return await self._read_repo.list_user_sessions(
            user_id=query.user_id,
            offset=offset,
            limit=query.size,
            page=query.page,
            size=query.size,
        )
