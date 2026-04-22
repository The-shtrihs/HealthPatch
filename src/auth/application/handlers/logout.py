from src.auth.application.commands import LogoutAllCommand, LogoutCommand
from src.auth.domain.interfaces import IRefreshTokenRepository


class LogoutCommandHandler:
    def __init__(self, token_repo: IRefreshTokenRepository):
        self._token_repo = token_repo

    async def handle(self, cmd: LogoutCommand) -> None:
        db_token = await self._token_repo.get_active_token(cmd.refresh_token)
        if db_token:
            db_token.revoke()
            await self._token_repo.save(db_token)

    async def handle_all(self, cmd: LogoutAllCommand) -> None:
        await self._token_repo.revoke_all_for_user(cmd.user_id)
