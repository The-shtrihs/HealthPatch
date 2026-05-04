from src.activity.application.commands import CreateWorkoutPlanCommand
from src.activity.domain.errors import ExerciseNotFoundError
from src.activity.domain.events import WorkoutPlanCreated
from src.activity.domain.factory import PlanTrainingExerciseFactory, WorkoutPlanFactory
from src.activity.domain.interfaces import IActivityUnitOfWork


class CreateWorkoutPlanCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: CreateWorkoutPlanCommand) -> int:
        async with self._uow:
            factory = WorkoutPlanFactory()
            draft = factory.create(
                author_id=cmd.author_id,
                title=cmd.title,
                description=cmd.description,
                is_public=cmd.is_public,
            )
            plan = await self._uow.repo.create_plan(
                author_id=draft.author_id,
                title=draft.title,
                description=draft.description,
                is_public=draft.is_public,
            )

            pte_factory = PlanTrainingExerciseFactory(self._uow.repo)

            for t in cmd.trainings:
                for ex in t.exercises:
                    if await self._uow.repo.get_exercise_by_id(ex.exercise_id) is None:
                        raise ExerciseNotFoundError(ex.exercise_id)

                training = await self._uow.repo.add_training(
                    plan_id=plan.id,
                    name=t.name,
                    weekday=t.weekday,
                    order_num=t.order_num,
                )
                for ex in t.exercises:
                    await pte_factory.create(
                        plan_training_id=training.id,
                        exercise_id=ex.exercise_id,
                        order_num=ex.order_num,
                        target_sets=ex.target_sets,
                        target_reps=ex.target_reps,
                        target_weight_pct=ex.target_weight_pct,
                    )
                    await self._uow.repo.add_exercise_to_training(
                        plan_training_id=training.id,
                        exercise_id=ex.exercise_id,
                        order_num=ex.order_num,
                        target_sets=ex.target_sets,
                        target_reps=ex.target_reps,
                        target_weight_pct=ex.target_weight_pct,
                    )

            self._uow.events.append(
                WorkoutPlanCreated(
                    plan_id=plan.id,
                    author_id=plan.author_id,
                    title=plan.title,
                    is_public=plan.is_public,
                )
            )

        return plan.id
