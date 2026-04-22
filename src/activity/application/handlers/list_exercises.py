from src.activity.application.queries import ListExercisesQuery
from src.activity.application.read_models import ExerciseReadModel, PageReadModel
from src.activity.infrastructure.read_repository import SqlAlchemyActivityReadRepository


class ListExercisesQueryHandler:
    def __init__(self, read_repo: SqlAlchemyActivityReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: ListExercisesQuery) -> PageReadModel[ExerciseReadModel]:
        offset = (query.page - 1) * query.size
        return await self._read_repo.list_exercises(
            search=query.search,
            offset=offset,
            limit=query.size,
            page=query.page,
            size=query.size,
        )
