from src.activity.application.commands import DeleteTrainingExerciseCommand
from src.activity.domain.errors import (
    NotResourceOwnerError,
    PlanTrainingExerciseNotFoundError,
    PlanTrainingNotFoundError,
    WorkoutPlanNotFoundError,
)
from src.activity.domain.interfaces import IActivityUnitOfWork


class DeleteTrainingExerciseCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: DeleteTrainingExerciseCommand) -> None:
        async with self._uow:
            plan = await self._uow.repo.get_plan_by_id(cmd.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError(cmd.plan_id)
            if not plan.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this workout plan")

            training = await self._uow.repo.get_training_by_id(cmd.training_id)
            if training is None or training.plan_id != cmd.plan_id:
                raise PlanTrainingNotFoundError(cmd.training_id)

            pte = await self._uow.repo.get_training_exercise_by_id(cmd.pte_id)
            if pte is None or pte.plan_training_id != cmd.training_id:
                raise PlanTrainingExerciseNotFoundError(cmd.pte_id)

            await self._uow.repo.delete_training_exercise(cmd.pte_id)
