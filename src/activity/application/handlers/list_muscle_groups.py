from src.activity.application.queries import ListMuscleGroupsQuery
from src.activity.application.read_models import MuscleGroupReadModel
from src.activity.infrastructure.read_repository import SqlAlchemyActivityReadRepository


class ListMuscleGroupsQueryHandler:
    def __init__(self, read_repo: SqlAlchemyActivityReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: ListMuscleGroupsQuery) -> list[MuscleGroupReadModel]:
        return await self._read_repo.list_muscle_groups()
