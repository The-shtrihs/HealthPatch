from src.activity.application.queries import GetPlanDetailQuery
from src.activity.application.read_models import WorkoutPlanDetailReadModel
from src.activity.domain.errors import PrivatePlanAccessError, WorkoutPlanNotFoundError
from src.activity.infrastructure.read_repository import SqlAlchemyActivityReadRepository


class GetPlanDetailQueryHandler:
    def __init__(self, read_repo: SqlAlchemyActivityReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: GetPlanDetailQuery) -> WorkoutPlanDetailReadModel:
        visibility = await self._read_repo.get_plan_visibility(query.plan_id)
        if visibility is None:
            raise WorkoutPlanNotFoundError(query.plan_id)
        author_id, is_public = visibility
        if not is_public and author_id != query.viewer_id:
            raise PrivatePlanAccessError()

        plan = await self._read_repo.get_plan_detail(query.plan_id)
        if plan is None:
            raise WorkoutPlanNotFoundError(query.plan_id)
        return plan
