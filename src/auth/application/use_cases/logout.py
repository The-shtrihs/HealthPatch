from src.auth.domain.interfaces import IRefreshTokenRepository


class LogoutUseCase:
    def __init__(self, token_repo: IRefreshTokenRepository):
        self._token_repo = token_repo

    async def execute(self, token: str) -> None:
        db_token = await self._token_repo.get_active_token(token)
        if db_token:
            db_token.revoke()
            await self._token_repo.save(db_token)

    async def execute_all(self, user_id: int) -> None:
        await self._token_repo.revoke_all_for_user(user_id)
