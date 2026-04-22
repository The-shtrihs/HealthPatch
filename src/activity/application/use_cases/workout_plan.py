from src.activity.application.dto import (
    AddExerciseToTrainingCommand,
    AddTrainingCommand,
    CreateWorkoutPlanCommand,
    DeleteTrainingCommand,
    DeleteTrainingExerciseCommand,
    DeleteWorkoutPlanCommand,
    Page,
    UpdateWorkoutPlanCommand,
)
from src.activity.domain.errors import (
    ExerciseNotFoundError,
    NotResourceOwnerError,
    PlanTrainingExerciseNotFoundError,
    PlanTrainingNotFoundError,
    PrivatePlanAccessError,
    WorkoutPlanNotFoundError,
)
from src.activity.domain.factory import (
    PlanTrainingExerciseFactory,
    WorkoutPlanFactory,
)
from src.activity.domain.interfaces import IActivityUnitOfWork
from src.activity.domain.models import (
    PlanTrainingDomain,
    PlanTrainingExerciseDomain,
    WorkoutPlanDomain,
)


class ListPublicPlansUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, page: int, size: int) -> Page[WorkoutPlanDomain]:
        offset = (page - 1) * size
        items, total = await self._uow.repo.list_public_plans(offset=offset, limit=size)
        return Page(items=items, total=total, page=page, size=size)


class ListUserPlansUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, user_id: int, page: int, size: int) -> Page[WorkoutPlanDomain]:
        offset = (page - 1) * size
        items, total = await self._uow.repo.list_user_plans(user_id=user_id, offset=offset, limit=size)
        return Page(items=items, total=total, page=page, size=size)


class GetPlanUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, plan_id: int, requesting_user_id: int) -> WorkoutPlanDomain:
        plan = await self._uow.repo.get_plan_with_trainings(plan_id)
        if plan is None:
            raise WorkoutPlanNotFoundError(plan_id)
        if not plan.is_visible_to(requesting_user_id):
            raise PrivatePlanAccessError()
        return plan


class CreatePlanUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: CreateWorkoutPlanCommand) -> WorkoutPlanDomain:
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
                # validate all exercises first for the training
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

        full = await self._uow.repo.get_plan_with_trainings(plan.id)
        if full is None:
            raise WorkoutPlanNotFoundError(plan.id)
        return full


class UpdatePlanUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: UpdateWorkoutPlanCommand) -> WorkoutPlanDomain:
        async with self._uow:
            plan = await self._uow.repo.get_plan_by_id(cmd.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError(cmd.plan_id)
            if not plan.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this workout plan")

            plan.update_details(
                title=cmd.title,
                description=cmd.description,
                is_public=cmd.is_public,
            )
            return await self._uow.repo.save_plan(plan)


class DeletePlanUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: DeleteWorkoutPlanCommand) -> None:
        async with self._uow:
            plan = await self._uow.repo.get_plan_by_id(cmd.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError(cmd.plan_id)
            if not plan.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this workout plan")
            await self._uow.repo.delete_plan(cmd.plan_id)


class AddTrainingUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: AddTrainingCommand) -> PlanTrainingDomain:
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

        full = await self._uow.repo.get_training_with_exercises(training.id)
        return full if full is not None else training


class DeleteTrainingUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: DeleteTrainingCommand) -> None:
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


class AddExerciseToTrainingUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: AddExerciseToTrainingCommand) -> PlanTrainingExerciseDomain:
        async with self._uow:
            plan = await self._uow.repo.get_plan_by_id(cmd.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError(cmd.plan_id)
            if not plan.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this workout plan")

            training = await self._uow.repo.get_training_by_id(cmd.training_id)
            if training is None or training.plan_id != cmd.plan_id:
                raise PlanTrainingNotFoundError(cmd.training_id)

            # Factory validates that the exercise exists (DB invariant).
            factory = PlanTrainingExerciseFactory(self._uow.repo)
            await factory.create(
                plan_training_id=cmd.training_id,
                exercise_id=cmd.exercise_id,
                order_num=cmd.order_num,
                target_sets=cmd.target_sets,
                target_reps=cmd.target_reps,
                target_weight_pct=cmd.target_weight_pct,
            )

            return await self._uow.repo.add_exercise_to_training(
                plan_training_id=cmd.training_id,
                exercise_id=cmd.exercise_id,
                order_num=cmd.order_num,
                target_sets=cmd.target_sets,
                target_reps=cmd.target_reps,
                target_weight_pct=cmd.target_weight_pct,
            )


class DeleteTrainingExerciseUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: DeleteTrainingExerciseCommand) -> None:
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
