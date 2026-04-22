from src.auth.application.queries import GetMeQuery
from src.auth.application.read_models import UserReadModel


class GetMeQueryHandler:
    def handle(self, query: GetMeQuery) -> UserReadModel:  # sync, без async
        u = query.user
        return UserReadModel(
            id=u.id,
            name=u.name,
            email=u.email,
            avatar_url=u.avatar_url,
            is_verified=u.is_verified,
            is_2fa_enabled=u.is_2fa_enabled,
            oauth_provider=u.oauth_provider,
        )
