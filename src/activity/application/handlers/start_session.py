from datetime import UTC, datetime

from src.activity.application.commands import StartSessionCommand
from src.activity.domain.errors import (
    PlanTrainingNotFoundError,
    PrivatePlanAccessError,
    WorkoutPlanNotFoundError,
)
from src.activity.domain.events import WorkoutSessionStarted
from src.activity.domain.factory import WorkoutSessionFactory
from src.activity.domain.interfaces import IActivityUnitOfWork


class StartSessionCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: StartSessionCommand) -> int:
        async with self._uow:
            factory = WorkoutSessionFactory(self._uow.repo)

            training = None
            if cmd.plan_training_id is not None:
                training = await self._uow.repo.get_training_with_exercises(cmd.plan_training_id)
                if training is None:
                    raise PlanTrainingNotFoundError(cmd.plan_training_id)
                plan = await self._uow.repo.get_plan_by_id(training.plan_id)
                if plan is None:
                    raise WorkoutPlanNotFoundError(training.plan_id)
                if not plan.is_visible_to(cmd.user_id):
                    raise PrivatePlanAccessError("This training belongs to a private plan")

            started_at = datetime.now(UTC)
            draft = await factory.start(
                user_id=cmd.user_id,
                plan_training_id=cmd.plan_training_id,
                at=started_at,
            )

            session = await self._uow.repo.create_session(
                user_id=draft.user_id,
                plan_training_id=draft.plan_training_id,
                started_at=draft.started_at,
            )

            if training is not None:
                for pte in sorted(training.exercises, key=lambda x: x.order_num):
                    await self._uow.repo.add_exercise_to_session(
                        workout_session_id=session.id,
                        exercise_id=pte.exercise_id,
                        order_num=pte.order_num,
                        is_from_template=True,
                    )

            self._uow.events.append(
                WorkoutSessionStarted(
                    session_id=session.id,
                    user_id=session.user_id,
                    plan_training_id=session.plan_training_id,
                    started_at=session.started_at,
                )
            )

        return session.id
