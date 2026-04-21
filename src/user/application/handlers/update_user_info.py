from src.user.application.commands import UpdateUserInfoCommand
from src.user.application.handlers.get_profile import _to_fitness_read_model
from src.user.application.read_models import FullProfileReadModel
from src.user.domain.errors import UserNotFoundError
from src.user.domain.interfaces import IUserProfileRepository


class UpdateUserInfoCommandHandler:
    def __init__(self, repo: IUserProfileRepository):
        self._repo = repo

    async def handle(self, cmd: UpdateUserInfoCommand) -> FullProfileReadModel:
        profile = await self._repo.get_full_profile(cmd.user_id)
        if not profile:
            raise UserNotFoundError(cmd.user_id)
        profile.update_info(name=cmd.name, avatar_url=cmd.avatar_url)
        saved = await self._repo.save_user_info(cmd.user_id, profile.name, profile.avatar_url)
        return FullProfileReadModel(
            id=saved.id,
            name=saved.name,
            email=saved.email,
            avatar_url=saved.avatar_url,
            is_verified=saved.is_verified,
            is_2fa_enabled=saved.is_2fa_enabled,
            oauth_provider=saved.oauth_provider,
            fitness=_to_fitness_read_model(saved.fitness),
        )