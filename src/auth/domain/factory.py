from src.auth.domain.errors import EmailAlreadyExistsError
from src.auth.domain.interfaces import IUserRepository
from src.auth.domain.models import UserDomain


class UserFactory:
    def __init__(self, user_repo: IUserRepository):
        self._repo = user_repo

    async def create_regular(self, name: str, email: str, password_hash: str) -> UserDomain:
        if await self._repo.get_by_email(email):
            raise EmailAlreadyExistsError()

        return UserDomain(
            id=None, 
            name=name,
            email=email,
            password_hash=password_hash,
            is_verified=False,   
            is_active=True,
            oauth_provider=None,
            oauth_provider_id=None,
            avatar_url=None,
            totp_secret=None,
            is_2fa_enabled=False,
        )

    def create_oauth(
        self,
        name: str,
        email: str,
        provider: str,
        provider_id: str,
        avatar_url: str | None = None,
    ) -> UserDomain:
        
        return UserDomain(
            id=None,
            name=name,
            email=email,
            password_hash=None,   
            is_verified=True,     
            is_active=True,
            oauth_provider=provider,
            oauth_provider_id=provider_id,
            avatar_url=avatar_url,
            totp_secret=None,
            is_2fa_enabled=False,
        )