from datetime import UTC, datetime

from src.nutrition.application.commands import AddMealEntryCommand
from src.nutrition.domain.interfaces import INutritionUnitOfWork
from src.nutrition.domain.models import MealEntryCreateDomain

from ._shared import require_profile


class AddMealEntryCommandHandler:
    def __init__(self, uow: INutritionUnitOfWork):
        self._uow = uow

    async def handle(self, command: AddMealEntryCommand) -> int:
        create = MealEntryCreateDomain(
            food_id=command.food_id,
            meal_type=command.meal_type,
            weight_grams=command.weight_grams,
            target_date=command.target_date,
        )

        create.validate()

        meal_type = create.normalized_meal_type()
        day = create.target_date or datetime.now(UTC).date()

        async with self._uow:
            await require_profile(self._uow, command.user_id)

            diary_id = await self._uow.repo.ensure_daily_diary(command.user_id, day)
            meal_entry_id = await self._uow.repo.add_meal_entry(
                diary_id=diary_id,
                food_id=create.food_id,
                meal_type=meal_type,
                weight_grams=create.weight_grams,
            )
            return meal_entry_id
