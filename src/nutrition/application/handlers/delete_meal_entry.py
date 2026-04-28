from src.nutrition.application.commands import DeleteMealEntryCommand
from src.nutrition.domain.errors import MealEntryNotFoundError
from src.nutrition.domain.interfaces import INutritionUnitOfWork

from ._shared import require_profile


class DeleteMealEntryCommandHandler:
    def __init__(self, uow: INutritionUnitOfWork):
        self._uow = uow

    async def handle(self, command: DeleteMealEntryCommand) -> int:
        async with self._uow:
            await require_profile(self._uow.repo, command.user_id)

            target_date = await self._uow.repo.get_user_meal_entry_target_date(command.user_id, command.meal_entry_id)
            if target_date is None:
                raise MealEntryNotFoundError(command.meal_entry_id)

            await self._uow.repo.delete_meal_entry(command.meal_entry_id)
            return command.meal_entry_id
