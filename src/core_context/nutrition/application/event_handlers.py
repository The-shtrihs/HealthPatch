from __future__ import annotations

import logging

from src.core_context.nutrition.domain.events import DailyDiaryUpdatedEvent, MealEntryAddedEvent, MealEntryDeletedEvent, MealEntryUpdatedEvent
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


def register_nutrition_event_handlers(bus: IEventBus) -> None:
    """Side-effect handlers for the nutrition domain (logging only).

    Audit persistence is handled separately by the analytics_context audit
    writer, which subscribes to integration events on the same bus.
    """

    @bus.subscribe(MealEntryAddedEvent)
    async def on_meal_entry_added(event: MealEntryAddedEvent) -> None:
        logger.info(
            "Nutrition | MealEntryAdded user_id=%d diary_id=%d meal_entry_id=%d target_date=%s",
            event.user_id,
            event.diary_id,
            event.meal_entry_id,
            event.target_date,
        )

    @bus.subscribe(MealEntryUpdatedEvent)
    async def on_meal_entry_updated(event: MealEntryUpdatedEvent) -> None:
        logger.info(
            "Nutrition | MealEntryUpdated user_id=%d meal_entry_id=%d target_date=%s",
            event.user_id,
            event.meal_entry_id,
            event.target_date,
        )

    @bus.subscribe(MealEntryDeletedEvent)
    async def on_meal_entry_deleted(event: MealEntryDeletedEvent) -> None:
        logger.info(
            "Nutrition | MealEntryDeleted user_id=%d meal_entry_id=%d target_date=%s",
            event.user_id,
            event.meal_entry_id,
            event.target_date,
        )

    @bus.subscribe(DailyDiaryUpdatedEvent)
    async def on_daily_diary_updated(event: DailyDiaryUpdatedEvent) -> None:
        logger.info(
            "Nutrition | DailyDiaryUpdated user_id=%d diary_id=%d target_date=%s",
            event.user_id,
            event.diary_id,
            event.target_date,
        )
