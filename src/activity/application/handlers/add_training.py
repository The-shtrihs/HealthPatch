from src.activity.application.commands import AddTrainingCommand
from src.activity.domain.errors import NotResourceOwnerError, WorkoutPlanNotFoundError
from src.activity.domain.interfaces import IActivityUnitOfWork


class AddTrainingCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: AddTrainingCommand) -> int:
        async with self._uow:
            plan = await self._uow.repo.get_plan_by_id(cmd.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError(cmd.plan_id)
            if not plan.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this workout plan")
            training = await self._uow.repo.add_training(
                plan_id=cmd.plan_id,
                name=cmd.name,
                weekday=cmd.weekday,
                order_num=cmd.order_num,
            )
        return training.id
