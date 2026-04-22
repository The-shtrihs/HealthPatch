from datetime import UTC, datetime

from src.activity.application.commands import LogSetCommand
from src.activity.domain.errors import (
    ExerciseSessionNotFoundError,
    NotResourceOwnerError,
    WorkoutSessionNotFoundError,
)
from src.activity.domain.factory import WorkoutSetFactory
from src.activity.domain.interfaces import IActivityUnitOfWork
from src.activity.domain.models import WeightKg


class LogSetCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: LogSetCommand) -> int:
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

        return ws.id
