from src.core_context.activity.application.queries import GetExerciseQuery
from src.core_context.activity.application.read_models import ExerciseReadModel
from src.core_context.activity.domain.errors import ExerciseNotFoundError
from src.core_context.activity.infrastructure.read_repository import SqlAlchemyActivityReadRepository


class GetExerciseQueryHandler:
    def __init__(self, read_repo: SqlAlchemyActivityReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: GetExerciseQuery) -> ExerciseReadModel:
        exercise = await self._read_repo.get_exercise(query.exercise_id)
        if exercise is None:
            raise ExerciseNotFoundError(query.exercise_id)
        return exercise
