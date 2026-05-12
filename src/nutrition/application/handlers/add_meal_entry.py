from datetime import UTC, datetime

from src.nutrition.application.commands import AddMealEntryCommand
from src.nutrition.domain.events import MealEntryAddedEvent
from src.nutrition.domain.interfaces import INutritionUnitOfWork
from src.nutrition.domain.models import MealEntryCreateDomain
from src.shared.application.dispatcher import dispatch_domain_events
from src.shared.infrastructure.event_bus_interface import IEventBus

from ._shared import require_profile


class AddMealEntryCommandHandler:
    def __init__(self, uow: INutritionUnitOfWork, bus: IEventBus):
        self._uow = uow
        self._bus = bus

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
            await require_profile(self._uow.repo, command.user_id)

            diary_id = await self._uow.repo.ensure_daily_diary(command.user_id, day)
            meal_entry_id = await self._uow.repo.add_meal_entry(
                diary_id=diary_id,
                food_id=create.food_id,
                meal_type=meal_type,
                weight_grams=create.weight_grams,
            )
            self._uow.events.append(
                MealEntryAddedEvent(
                    user_id=command.user_id,
                    diary_id=diary_id,
                    meal_entry_id=meal_entry_id,
                    food_id=create.food_id,
                    meal_type=meal_type,
                    weight_grams=create.weight_grams,
                    target_date=day,
                )
            )
        await dispatch_domain_events(self._uow, self._bus)
        return meal_entry_id
