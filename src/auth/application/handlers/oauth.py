from src.auth.application.commands import HandleOAuthUserCommand
from src.auth.application.read_models import TokenReadModel
from src.auth.application.token_utils import TokenUtils, issue_refresh_token
from src.auth.domain.factory import UserFactory
from src.auth.domain.interfaces import IRefreshTokenRepository, IUserRepository
from src.core.config import get_settings
from src.core.constants import SECONDS_PER_MINUTE


class HandleOAuthUserCommandHandler:
    def __init__(self, user_repo: IUserRepository, token_repo: IRefreshTokenRepository):
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._factory = UserFactory(user_repo)
        self._settings = get_settings()

    async def handle(self, cmd: HandleOAuthUserCommand) -> TokenReadModel:
        user = await self._user_repo.get_by_oauth(cmd.provider, cmd.provider_id)

        if not user:
            user = await self._user_repo.get_by_email(cmd.email)
            if user:
                user.oauth_provider = cmd.provider
                user.oauth_provider_id = cmd.provider_id
                if cmd.avatar_url:
                    user.avatar_url = cmd.avatar_url
                user = await self._user_repo.save(user)
            else:
                oauth_user = self._factory.create_oauth(
                    name=cmd.name,
                    email=cmd.email,
                    provider=cmd.provider,
                    provider_id=cmd.provider_id,
                    avatar_url=cmd.avatar_url,
                )
                user = await self._user_repo.create(
                    name=oauth_user.name,
                    email=oauth_user.email,
                    password_hash=None,
                    provider=cmd.provider,
                    provider_id=cmd.provider_id,
                    avatar_url=cmd.avatar_url,
                )

        refresh_token = await issue_refresh_token(self._token_repo, user.id, device_info=None)
        return TokenReadModel(
            access_token=TokenUtils.create_access_token(user.id, user.email),
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self._settings.access_token_expire_minutes * SECONDS_PER_MINUTE,
        )
