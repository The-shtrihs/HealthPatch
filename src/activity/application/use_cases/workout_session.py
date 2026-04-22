from datetime import UTC, datetime

from src.activity.application.dto import (
    AddExerciseToSessionCommand,
    EndSessionCommand,
    LogSetCommand,
    Page,
    StartSessionCommand,
)
from src.activity.domain.errors import (
    ExerciseSessionNotFoundError,
    NotResourceOwnerError,
    PlanTrainingNotFoundError,
    PrivatePlanAccessError,
    WorkoutPlanNotFoundError,
    WorkoutSessionNotFoundError,
)
from src.activity.domain.factory import (
    ExerciseSessionFactory,
    WorkoutSessionFactory,
    WorkoutSetFactory,
)
from src.activity.domain.interfaces import IActivityUnitOfWork
from src.activity.domain.models import (
    ExerciseSessionDomain,
    WeightKg,
    WorkoutSessionDomain,
    WorkoutSetDomain,
)


class StartSessionUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: StartSessionCommand) -> WorkoutSessionDomain:
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

            # Factory also validates existence; here we've already loaded it.
            started_at = datetime.now(UTC)
            # Use the factory so invariants live in one place:
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

        return session


class EndSessionUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: EndSessionCommand) -> WorkoutSessionDomain:
        async with self._uow:
            session = await self._uow.repo.get_session_by_id(cmd.session_id)
            if session is None:
                raise WorkoutSessionNotFoundError(cmd.session_id)
            if not session.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this session")
            session.end(datetime.now(UTC))  # raises SessionAlreadyEndedError if already closed
            return await self._uow.repo.save_session(session)


class GetSessionDetailUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, session_id: int, user_id: int) -> WorkoutSessionDomain:
        session = await self._uow.repo.get_session_with_exercises(session_id)
        if session is None:
            raise WorkoutSessionNotFoundError(session_id)
        if not session.is_owned_by(user_id):
            raise NotResourceOwnerError("You do not own this session")
        return session


class ListUserSessionsUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, user_id: int, page: int, size: int) -> Page[WorkoutSessionDomain]:
        offset = (page - 1) * size
        items, total = await self._uow.repo.list_user_sessions(user_id=user_id, offset=offset, limit=size)
        return Page(items=items, total=total, page=page, size=size)


class AddExerciseToSessionUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: AddExerciseToSessionCommand) -> ExerciseSessionDomain:
        async with self._uow:
            session = await self._uow.repo.get_session_by_id(cmd.session_id)
            if session is None:
                raise WorkoutSessionNotFoundError(cmd.session_id)
            if not session.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this session")
            session.ensure_can_be_modified("Cannot add exercises to an ended session")

            factory = ExerciseSessionFactory(self._uow.repo)
            await factory.create(
                workout_session_id=cmd.session_id,
                exercise_id=cmd.exercise_id,
                order_num=cmd.order_num,
                is_from_template=False,
            )

            return await self._uow.repo.add_exercise_to_session(
                workout_session_id=cmd.session_id,
                exercise_id=cmd.exercise_id,
                order_num=cmd.order_num,
                is_from_template=False,
            )


class LogSetUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: LogSetCommand) -> WorkoutSetDomain:
        async with self._uow:
            session = await self._uow.repo.get_session_by_id(cmd.session_id)
            if session is None:
                raise WorkoutSessionNotFoundError(cmd.session_id)
            if not session.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this session")
            session.ensure_can_be_modified("Cannot log sets on an ended session")

            es = await self._uow.repo.get_exercise_session_by_id(cmd.exercise_session_id)
            if es is None or es.workout_session_id != cmd.session_id:
                raise ExerciseSessionNotFoundError(cmd.exercise_session_id)

            # Factory validates VOs (reps > 0, weight >= 0, set_number > 0) + parent session open.
            factory = WorkoutSetFactory(self._uow.repo)
            await factory.log(
                exercise_session_id=cmd.exercise_session_id,
                set_number=cmd.set_number,
                reps=cmd.reps,
                weight=cmd.weight,
            )

            ws = await self._uow.repo.add_set(
                exercise_session_id=cmd.exercise_session_id,
                set_number=cmd.set_number,
                reps=cmd.reps,
                weight=cmd.weight,
            )

            # Auto-bump personal record if this set beats it.
            weight_vo = WeightKg(cmd.weight)
            if weight_vo.value > 0:
                existing = await self._uow.repo.get_personal_record(cmd.user_id, es.exercise_id)
                if existing is None or weight_vo.is_greater_than(existing.weight):
                    await self._uow.repo.upsert_personal_record(
                        user_id=cmd.user_id,
                        exercise_id=es.exercise_id,
                        weight=cmd.weight,
                        recorded_at=datetime.now(UTC),
                    )

        return ws
