from datetime import UTC, datetime

from src.auth.application.commands import RefreshTokenCommand
from src.auth.application.read_models import TokenReadModel
from src.auth.application.token_utils import TokenUtils, issue_refresh_token
from src.auth.domain.errors import InvalidTokenError, UserInactiveError
from src.auth.domain.interfaces import IRefreshTokenRepository, IUserRepository
from src.core.config import get_settings
from src.core.constants import SECONDS_PER_MINUTE


class RefreshTokenCommandHandler:
    def __init__(self, user_repo: IUserRepository, token_repo: IRefreshTokenRepository):
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._settings = get_settings()

    async def handle(self, cmd: RefreshTokenCommand) -> TokenReadModel:
        db_token = await self._token_repo.get_active_token(cmd.refresh_token)
        if not db_token:
            raise InvalidTokenError("Invalid refresh token")
        if db_token.is_expired(datetime.now(UTC)):
            db_token.revoke()
            await self._token_repo.save(db_token)
            raise InvalidTokenError("Refresh token has expired")

        user = await self._user_repo.get_by_id(db_token.user_id)
        if not user or not user.is_active:
            raise UserInactiveError()

        db_token.revoke()
        await self._token_repo.save(db_token)

        new_refresh = await issue_refresh_token(self._token_repo, user.id, device_info=None)
        return TokenReadModel(
            access_token=TokenUtils.create_access_token(user.id, user.email),
            refresh_token=new_refresh,
            token_type="bearer",
            expires_in=self._settings.access_token_expire_minutes * SECONDS_PER_MINUTE,
        )