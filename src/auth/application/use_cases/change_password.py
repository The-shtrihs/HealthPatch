from src.auth.application.token_utils import PasswordUtils
from src.auth.domain.errors import PasswordMismatchError, UserNotFoundError
from src.auth.domain.interfaces import IRefreshTokenRepository, IUserRepository


class ChangePasswordUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: IRefreshTokenRepository,
        password_utils: PasswordUtils,
    ):
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._pw = password_utils

    async def execute(self, user_id: int, current_password: str, new_password: str) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        if not self._pw.verify(current_password, user.password_hash):
            raise PasswordMismatchError()
        user.change_password(self._pw.hash(new_password))
        await self._user_repo.save(user)
        await self._token_repo.revoke_all_for_user(user_id)