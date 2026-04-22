from datetime import UTC, datetime

from src.activity.application.dto import (
    DeletePersonalRecordCommand,
    UpsertPersonalRecordCommand,
)
from src.activity.domain.errors import (
    NotResourceOwnerError,
    PersonalRecordNotFoundError,
)
from src.activity.domain.factory import PersonalRecordFactory
from src.activity.domain.interfaces import IActivityUnitOfWork
from src.activity.domain.models import PersonalRecordDomain


class ListPersonalRecordsUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, user_id: int) -> list[PersonalRecordDomain]:
        return await self._uow.repo.list_user_personal_records(user_id)


class UpsertPersonalRecordUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: UpsertPersonalRecordCommand) -> PersonalRecordDomain:
        async with self._uow:
            factory = PersonalRecordFactory(self._uow.repo)
            # Factory enforces: exercise exists + no downgrade.
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
        return pr


class DeletePersonalRecordUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: DeletePersonalRecordCommand) -> int:
        async with self._uow:
            pr = await self._uow.repo.get_personal_record_by_id(cmd.pr_id)
            if pr is None:
                raise PersonalRecordNotFoundError(cmd.pr_id)
            if not pr.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this personal record")
            await self._uow.repo.delete_personal_record(cmd.pr_id)
        return cmd.pr_id
