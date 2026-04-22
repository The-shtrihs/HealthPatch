from src.activity.application.commands import DeleteTrainingCommand
from src.activity.domain.errors import (
    NotResourceOwnerError,
    PlanTrainingNotFoundError,
    WorkoutPlanNotFoundError,
)
from src.activity.domain.interfaces import IActivityUnitOfWork


class DeleteTrainingCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: DeleteTrainingCommand) -> None:
        async with self._uow:
            plan = await self._uow.repo.get_plan_by_id(cmd.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError(cmd.plan_id)
            if not plan.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this workout plan")
            training = await self._uow.repo.get_training_by_id(cmd.training_id)
            if training is None or training.plan_id != cmd.plan_id:
                raise PlanTrainingNotFoundError(cmd.training_id)
            await self._uow.repo.delete_training(cmd.training_id)
