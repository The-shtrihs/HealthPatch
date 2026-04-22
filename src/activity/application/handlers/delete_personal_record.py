from src.activity.application.commands import DeletePersonalRecordCommand
from src.activity.domain.errors import NotResourceOwnerError, PersonalRecordNotFoundError
from src.activity.domain.interfaces import IActivityUnitOfWork


class DeletePersonalRecordCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: DeletePersonalRecordCommand) -> None:
        async with self._uow:
            pr = await self._uow.repo.get_personal_record_by_id(cmd.pr_id)
            if pr is None:
                raise PersonalRecordNotFoundError(cmd.pr_id)
            if not pr.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this personal record")
            await self._uow.repo.delete_personal_record(cmd.pr_id)
