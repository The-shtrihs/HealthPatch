from src.activity.application.queries import GetSessionDetailQuery
from src.activity.application.read_models import WorkoutSessionDetailReadModel
from src.activity.domain.errors import NotResourceOwnerError, WorkoutSessionNotFoundError
from src.activity.infrastructure.read_repository import SqlAlchemyActivityReadRepository


class GetSessionDetailQueryHandler:
    def __init__(self, read_repo: SqlAlchemyActivityReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: GetSessionDetailQuery) -> WorkoutSessionDetailReadModel:
        owner = await self._read_repo.get_session_owner(query.session_id)
        if owner is None:
            raise WorkoutSessionNotFoundError(query.session_id)
        if owner != query.user_id:
            raise NotResourceOwnerError("You do not own this session")

        session = await self._read_repo.get_session_detail(query.session_id)
        if session is None:
            raise WorkoutSessionNotFoundError(query.session_id)
        return session
