from src.activity.application.queries import ListPersonalRecordsQuery
from src.activity.application.read_models import PersonalRecordReadModel
from src.activity.infrastructure.read_repository import SqlAlchemyActivityReadRepository


class ListPersonalRecordsQueryHandler:
    def __init__(self, read_repo: SqlAlchemyActivityReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: ListPersonalRecordsQuery) -> list[PersonalRecordReadModel]:
        return await self._read_repo.list_user_personal_records(query.user_id)
