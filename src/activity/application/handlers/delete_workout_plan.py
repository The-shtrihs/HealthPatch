from src.activity.application.commands import DeleteWorkoutPlanCommand
from src.activity.domain.errors import NotResourceOwnerError, WorkoutPlanNotFoundError
from src.activity.domain.events import WorkoutPlanDeleted
from src.activity.domain.interfaces import IActivityUnitOfWork


class DeleteWorkoutPlanCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: DeleteWorkoutPlanCommand) -> None:
        async with self._uow:
            plan = await self._uow.repo.get_plan_by_id(cmd.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError(cmd.plan_id)
            if not plan.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this workout plan")
            await self._uow.repo.delete_plan(cmd.plan_id)
            self._uow.events.append(
                WorkoutPlanDeleted(
                    plan_id=plan.id,
                    author_id=plan.author_id,
                )
            )
