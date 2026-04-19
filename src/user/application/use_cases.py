from src.user.application.dto import UpdateFitnessCommand, UpdateUserInfoCommand
from src.user.domain.errors import UserNotFoundError
from src.user.domain.interfaces import IUserProfileRepository
from src.user.domain.models import FitnessProfileDomain, UserProfileDomain


class UserProfileUseCases:
    def __init__(self, repo: IUserProfileRepository):
        self._repo = repo

    async def get_profile(self, user_id: int) -> UserProfileDomain:
        profile = await self._repo.get_full_profile(user_id)
        if not profile:
            raise UserNotFoundError(user_id)
        return profile

    async def update_info(self, user_id: int, cmd: UpdateUserInfoCommand) -> UserProfileDomain:
        profile = await self.get_profile(user_id)
        profile.update_info(name=cmd.name, avatar_url=cmd.avatar_url)
        return await self._repo.save_user_info(user_id, profile.name, profile.avatar_url)

    async def update_fitness(self, user_id: int, cmd: UpdateFitnessCommand) -> FitnessProfileDomain:
        profile = await self.get_profile(user_id)
        profile.update_fitness(
            weight=cmd.weight,
            height=cmd.height,
            age=cmd.age,
            gender=cmd.gender,
            fitness_goal=cmd.fitness_goal,
        )
        return await self._repo.save_fitness(user_id, profile.fitness)

    async def delete_account(self, user_id: int) -> None:
        await self._repo.deactivate(user_id)
