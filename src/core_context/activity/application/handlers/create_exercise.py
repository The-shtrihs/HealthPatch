from src.core_context.activity.application.commands import CreateExerciseCommand
from src.core_context.activity.domain.factory import ExerciseFactory
from src.core_context.activity.domain.interfaces import IActivityUnitOfWork


class CreateExerciseCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: CreateExerciseCommand) -> int:
        async with self._uow:
            factory = ExerciseFactory(self._uow.repo)
            await factory.validate_muscle_groups(
                cmd.primary_muscle_group_id,
                cmd.secondary_muscle_group_ids,
            )
            exercise = await self._uow.repo.create_exercise(
                name=cmd.name.strip(),
                primary_muscle_group_id=cmd.primary_muscle_group_id,
                secondary_muscle_group_ids=cmd.secondary_muscle_group_ids,
            )
        return exercise.id
