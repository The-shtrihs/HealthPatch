from datetime import UTC, datetime

from src.activity.application.commands import UpsertPersonalRecordCommand
from src.activity.domain.factory import PersonalRecordFactory
from src.activity.domain.interfaces import IActivityUnitOfWork


class UpsertPersonalRecordCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: UpsertPersonalRecordCommand) -> int:
        async with self._uow:
            factory = PersonalRecordFactory(self._uow.repo)
            await factory.upsert(
                user_id=cmd.user_id,
                exercise_id=cmd.exercise_id,
                weight=cmd.weight,
                at=datetime.now(UTC),
            )
            pr = await self._uow.repo.upsert_personal_record(
                user_id=cmd.user_id,
                exercise_id=cmd.exercise_id,
                weight=cmd.weight,
                recorded_at=datetime.now(UTC),
            )
        return pr.id
