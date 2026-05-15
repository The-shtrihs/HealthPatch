from typing import Protocol, runtime_checkable

from src.core_context.activity.contracts.dtos import ExerciseDTO


@runtime_checkable
class IExerciseCatalog(Protocol):
    async def get(self, exercise_id: int) -> ExerciseDTO | None: ...

    async def list_all(self) -> list[ExerciseDTO]: ...
