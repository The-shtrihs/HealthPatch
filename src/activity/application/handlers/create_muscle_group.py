from src.activity.application.commands import CreateMuscleGroupCommand
from src.activity.domain.interfaces import IActivityUnitOfWork


class CreateMuscleGroupCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: CreateMuscleGroupCommand) -> int:
        async with self._uow:
            mg = await self._uow.repo.create_muscle_group(cmd.name.strip())
        return mg.id
