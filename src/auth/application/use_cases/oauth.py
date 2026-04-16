import secrets
from datetime import UTC, datetime, timedelta

from src.auth.application.dto import TokenResult
from src.auth.application.token_utils import TokenUtils, issue_refresh_token
from src.auth.domain.factory import UserFactory
from src.auth.domain.interfaces import IRefreshTokenRepository, IUserRepository
from src.core.config import get_settings
from src.core.constants import REFRESH_TOKEN_BYTES, SECONDS_PER_MINUTE


class HandleOAuthUserUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: IRefreshTokenRepository,
    ):
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._factory = UserFactory(user_repo)
        self._settings = get_settings()

    async def execute(
        self,
        provider: str,
        provider_id: str,
        email: str,
        name: str,
        avatar_url: str | None,
    ) -> TokenResult:
        user = await self._user_repo.get_by_oauth(provider, provider_id)

        if not user:
            user = await self._user_repo.get_by_email(email)
            if user:
                user.oauth_provider = provider
                user.oauth_provider_id = provider_id
                if avatar_url:
                    user.avatar_url = avatar_url
                user = await self._user_repo.save(user)
            else:
                oauth_user = self._factory.create_oauth(
                    name=name, email=email, provider=provider,
                    provider_id=provider_id, avatar_url=avatar_url,
                )
                user = await self._user_repo.create(
                    name=oauth_user.name, email=oauth_user.email,
                    password_hash=None, provider=provider,
                    provider_id=provider_id, avatar_url=avatar_url,
                )

        refresh_token = await issue_refresh_token(self._token_repo, user.id, device_info=None)

        return TokenResult(
            access_token=TokenUtils.create_access_token(user.id, user.email),
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self._settings.access_token_expire_minutes * SECONDS_PER_MINUTE,
        )