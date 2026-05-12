from src.nutrition.application.commands import UpdateMealEntryCommand
from src.nutrition.domain.errors import MealEntryNotFoundError
from src.nutrition.domain.events import MealEntryUpdatedEvent, DailyNormAchievedEvent
from src.nutrition.domain.calculations import calculate_daily_norm
from src.nutrition.domain.interfaces import INutritionUnitOfWork
from src.shared.application.dispatcher import dispatch_domain_events
from src.shared.infrastructure.event_bus_interface import IEventBus

from ._shared import require_profile


class UpdateMealEntryCommandHandler:
    def __init__(self, uow: INutritionUnitOfWork, bus: IEventBus):
        self._uow = uow
        self._bus = bus

    async def handle(self, command: UpdateMealEntryCommand) -> int:
        async with self._uow:
            await require_profile(self._uow.repo, command.user_id)

            target_date = await self._uow.repo.update_meal_entry(
                user_id=command.user_id,
                meal_entry_id=command.meal_entry_id,
                food_id=command.food_id,
                meal_type=command.meal_type,
                weight_grams=command.weight_grams,
            )
            if target_date is None:
                raise MealEntryNotFoundError(command.meal_entry_id)

            self._uow.events.append(
                MealEntryUpdatedEvent(
                    user_id=command.user_id,
                    meal_entry_id=command.meal_entry_id,
                    food_id=command.food_id,
                    meal_type=command.meal_type,
                    weight_grams=command.weight_grams,
                    target_date=target_date,
                )
            )
            try:
                totals = await self._uow.repo.get_day_consumed_totals(command.user_id, target_date)
                user_profile = await self._uow.repo.get_profile(command.user_id)
                if user_profile is not None:
                    norm = calculate_daily_norm(user_profile)
                    if float(totals.calories) >= norm.calories:
                        diary_id = await self._uow.repo.ensure_daily_diary(command.user_id, target_date)
                        self._uow.events.append(
                            DailyNormAchievedEvent(
                                user_id=command.user_id,
                                diary_id=diary_id,
                                target_date=target_date,
                            )
                        )
            except Exception:
                pass

        await dispatch_domain_events(self._uow, self._bus)
        return command.meal_entry_id