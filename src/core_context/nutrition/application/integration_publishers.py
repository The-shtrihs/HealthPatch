import logging

from src.core_context.nutrition.contracts import events as integration
from src.core_context.nutrition.domain.events import (
    DailyNormAchievedEvent,
    MealEntryAddedEvent,
    MealEntryDeletedEvent,
    MealEntryUpdatedEvent,
)
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


def register_nutrition_integration_publishers(bus: IEventBus) -> None:
    @bus.subscribe(MealEntryAddedEvent, mode="sync")
    async def _on_meal_added(event: MealEntryAddedEvent) -> None:
        await bus.publish(
            integration.MealEntryAdded(
                entry_id=event.meal_entry_id,
                user_id=event.user_id,
                consumed_on=event.target_date,
                meal_type=event.meal_type,
                weight_grams=event.weight_grams,
            )
        )

    @bus.subscribe(MealEntryUpdatedEvent, mode="sync")
    async def _on_meal_updated(event: MealEntryUpdatedEvent) -> None:
        await bus.publish(
            integration.MealEntryUpdated(
                entry_id=event.meal_entry_id,
                user_id=event.user_id,
                consumed_on=event.target_date,
            )
        )

    @bus.subscribe(MealEntryDeletedEvent, mode="sync")
    async def _on_meal_deleted(event: MealEntryDeletedEvent) -> None:
        await bus.publish(
            integration.MealEntryDeleted(
                entry_id=event.meal_entry_id,
                user_id=event.user_id,
                consumed_on=event.target_date,
            )
        )

    @bus.subscribe(DailyNormAchievedEvent, mode="sync")
    async def _on_daily_norm(event: DailyNormAchievedEvent) -> None:
        await bus.publish(
            integration.DailyNormAchieved(
                user_id=event.user_id,
                day=event.target_date,
            )
        )
