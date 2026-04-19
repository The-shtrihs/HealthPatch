from src.auth.application.dto import TokenResult
from src.auth.application.providers.dto import OAuthUserInfo
from src.auth.application.token_utils import TokenUtils, issue_refresh_token
from src.auth.domain.factory import UserFactory
from src.auth.domain.interfaces import IRefreshTokenRepository, IUserRepository
from src.core.config import get_settings
from src.core.constants import SECONDS_PER_MINUTE


class HandleOAuthUserUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: IRefreshTokenRepository,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._factory = UserFactory(user_repo)
        self._settings = get_settings()

    async def execute(self, info: OAuthUserInfo) -> TokenResult:
        user = await self._user_repo.get_by_oauth(info.provider, info.provider_id)

        if not user:
            user = await self._user_repo.get_by_email(info.email)
            if user:
                user.oauth_provider = info.provider
                user.oauth_provider_id = info.provider_id
                if info.avatar_url:
                    user.avatar_url = info.avatar_url
                user = await self._user_repo.save(user)
            else:
                oauth_domain = self._factory.create_oauth(
                    name=info.name,
                    email=info.email,
                    provider=info.provider,
                    provider_id=info.provider_id,
                    avatar_url=info.avatar_url,
                )
                user = await self._user_repo.create(
                    name=oauth_domain.name,
                    email=oauth_domain.email,
                    password_hash=None,
                    provider=info.provider,
                    provider_id=info.provider_id,
                    avatar_url=info.avatar_url,
                )

        refresh_token = await issue_refresh_token(self._token_repo, user.id, device_info=None)

        return TokenResult(
            access_token=TokenUtils.create_access_token(user.id, user.email),
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self._settings.access_token_expire_minutes * SECONDS_PER_MINUTE,
        )