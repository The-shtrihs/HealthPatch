from src.core.config import get_settings
from src.core.constants import SECONDS_PER_MINUTE, TWO_FA_TOKEN_EXPIRE_SECONDS
from src.core_context.auth.application.commands import LoginCommand
from src.core_context.auth.application.read_models import TokenReadModel
from src.core_context.auth.application.token_utils import PasswordUtils, TokenUtils, issue_refresh_token
from src.core_context.auth.domain.errors import InvalidCredentialsError, UserInactiveError
from src.core_context.auth.domain.interfaces import IRefreshTokenRepository, IUserRepository


class LoginCommandHandler:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: IRefreshTokenRepository,
        password_utils: PasswordUtils,
    ):
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._pw = password_utils
        self._settings = get_settings()

    async def handle(self, cmd: LoginCommand) -> TokenReadModel:
        user = await self._user_repo.get_by_email(cmd.email)
        if not user:
            raise InvalidCredentialsError()
        if not user.password_hash:
            raise InvalidCredentialsError("This email is registered with an OAuth provider.")
        if not self._pw.verify(cmd.password, user.password_hash):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise UserInactiveError()

        if user.is_2fa_enabled:
            return TokenReadModel(
                access_token=TokenUtils.create_2fa_token(user.id, user.email),
                refresh_token=None,
                token_type="2fa_required",
                expires_in=TWO_FA_TOKEN_EXPIRE_SECONDS,
            )

        refresh_token = await issue_refresh_token(self._token_repo, user.id, cmd.device_info)
        return TokenReadModel(
            access_token=TokenUtils.create_access_token(user.id, user.email),
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self._settings.access_token_expire_minutes * SECONDS_PER_MINUTE,
        )
