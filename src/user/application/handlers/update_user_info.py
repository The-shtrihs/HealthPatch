from src.user.application.commands import UpdateUserInfoCommand
from src.user.domain.errors import UserNotFoundError
from src.user.domain.interfaces import IUserProfileRepository


class UpdateUserInfoCommandHandler:
    def __init__(self, repo: IUserProfileRepository):
        self._repo = repo

    async def handle(self, cmd: UpdateUserInfoCommand) -> None:
        profile = await self._repo.get_by_id(cmd.user_id)
        if not profile:
            raise UserNotFoundError(cmd.user_id)
        profile.update_info(name=cmd.name, avatar_url=cmd.avatar_url)
        await self._repo.save_user_info(cmd.user_id, profile.name, profile.avatar_url)