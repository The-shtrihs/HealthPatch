from src.activity.application.dto import (
    CreateExerciseCommand,
    CreateMuscleGroupCommand,
    ListExercisesQuery,
    Page,
)
from src.activity.domain.errors import ExerciseNotFoundError
from src.activity.domain.factory import ExerciseFactory
from src.activity.domain.interfaces import IActivityUnitOfWork
from src.activity.domain.models import ExerciseDomain, MuscleGroupDomain


class ListMuscleGroupsUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self) -> list[MuscleGroupDomain]:
        return await self._uow.repo.list_muscle_groups()


class CreateMuscleGroupUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: CreateMuscleGroupCommand) -> MuscleGroupDomain:
        async with self._uow:
            return await self._uow.repo.create_muscle_group(cmd.name.strip())


class ListExercisesUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, query: ListExercisesQuery) -> Page[ExerciseDomain]:
        offset = (query.page - 1) * query.size
        items, total = await self._uow.repo.list_exercises(search=query.search, offset=offset, limit=query.size)
        return Page(items=items, total=total, page=query.page, size=query.size)


class GetExerciseUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, exercise_id: int) -> ExerciseDomain:
        exercise = await self._uow.repo.get_exercise_by_id(exercise_id)
        if exercise is None:
            raise ExerciseNotFoundError(exercise_id)
        return exercise


class CreateExerciseUseCase:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def execute(self, cmd: CreateExerciseCommand) -> ExerciseDomain:
        async with self._uow:
            factory = ExerciseFactory(self._uow.repo)
            await factory.validate_muscle_groups(
                cmd.primary_muscle_group_id,
                cmd.secondary_muscle_group_ids,
            )
            return await self._uow.repo.create_exercise(
                name=cmd.name.strip(),
                primary_muscle_group_id=cmd.primary_muscle_group_id,
                secondary_muscle_group_ids=cmd.secondary_muscle_group_ids,
            )
