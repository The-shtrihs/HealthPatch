from src.activity.application.commands import AddExerciseToTrainingCommand
from src.activity.domain.errors import (
    NotResourceOwnerError,
    PlanTrainingNotFoundError,
    WorkoutPlanNotFoundError,
)
from src.activity.domain.factory import PlanTrainingExerciseFactory
from src.activity.domain.interfaces import IActivityUnitOfWork


class AddExerciseToTrainingCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: AddExerciseToTrainingCommand) -> int:
        async with self._uow:
            plan = await self._uow.repo.get_plan_by_id(cmd.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError(cmd.plan_id)
            if not plan.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this workout plan")

            training = await self._uow.repo.get_training_by_id(cmd.training_id)
            if training is None or training.plan_id != cmd.plan_id:
                raise PlanTrainingNotFoundError(cmd.training_id)

            factory = PlanTrainingExerciseFactory(self._uow.repo)
            await factory.create(
                plan_training_id=cmd.training_id,
                exercise_id=cmd.exercise_id,
                order_num=cmd.order_num,
                target_sets=cmd.target_sets,
                target_reps=cmd.target_reps,
                target_weight_pct=cmd.target_weight_pct,
            )

            pte = await self._uow.repo.add_exercise_to_training(
                plan_training_id=cmd.training_id,
                exercise_id=cmd.exercise_id,
                order_num=cmd.order_num,
                target_sets=cmd.target_sets,
                target_reps=cmd.target_reps,
                target_weight_pct=cmd.target_weight_pct,
            )
        return pte.id
