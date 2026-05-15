from src.core_context.nutrition.application.commands import DeleteMealEntryCommand
from src.core_context.nutrition.domain.errors import MealEntryNotFoundError
from src.core_context.nutrition.domain.events import MealEntryDeletedEvent
from src.core_context.nutrition.domain.interfaces import INutritionUnitOfWork
from src.shared.application.dispatcher import dispatch_domain_events
from src.shared.infrastructure.event_bus_interface import IEventBus

from ._shared import require_profile


class DeleteMealEntryCommandHandler:
    def __init__(self, uow: INutritionUnitOfWork, bus: IEventBus):
        self._uow = uow
        self._bus = bus

    async def handle(self, command: DeleteMealEntryCommand) -> int:
        async with self._uow:
            await require_profile(self._uow.repo, command.user_id)

            target_date = await self._uow.repo.get_user_meal_entry_target_date(command.user_id, command.meal_entry_id)
            if target_date is None:
                raise MealEntryNotFoundError(command.meal_entry_id)

            await self._uow.repo.delete_meal_entry(command.meal_entry_id)
            self._uow.events.append(
                MealEntryDeletedEvent(
                    user_id=command.user_id,
                    meal_entry_id=command.meal_entry_id,
                    target_date=target_date,
                )
            )
        await dispatch_domain_events(self._uow, self._bus)
        return command.meal_entry_id
