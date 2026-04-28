from src.user.application.commands import UpdateFitnessCommand
from src.user.domain.errors import UserNotFoundError
from src.user.domain.interfaces import IUserProfileRepository


class UpdateFitnessCommandHandler:
    def __init__(self, repo: IUserProfileRepository):
        self._repo = repo

    async def handle(self, cmd: UpdateFitnessCommand) -> None:
        profile = await self._repo.get_by_id(cmd.user_id)
        if not profile:
            raise UserNotFoundError(cmd.user_id)
        profile.update_fitness(
            weight=cmd.weight,
            height=cmd.height,
            age=cmd.age,
            gender=cmd.gender,
            fitness_goal=cmd.fitness_goal,
        )
        await self._repo.save_fitness(cmd.user_id, profile.fitness)
