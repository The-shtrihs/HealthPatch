from dataclasses import dataclass
from src.user.application.commands import DeleteAccountCommand
from src.user.domain.interfaces import IUserProfileRepository

class DeleteAccountCommandHandler:
    def __init__(self, repo: IUserProfileRepository):
        self._repo = repo

    async def handle(self, cmd: DeleteAccountCommand) -> None:
        await self._repo.deactivate(cmd.user_id)