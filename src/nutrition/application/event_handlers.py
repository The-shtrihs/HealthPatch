from __future__ import annotations

import logging

from src.nutrition.application.audit_service import INutritionAuditService
from src.nutrition.domain.events import DailyDiaryUpdatedEvent, MealEntryAddedEvent, MealEntryDeletedEvent, MealEntryUpdatedEvent
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


def register_nutrition_event_handlers(bus: IEventBus, audit_service: INutritionAuditService) -> None:
    """Asynchronous audit path for the nutrition domain.

    Each subscriber forwards an immutable past-tense diary event to the audit
    service. Handlers are independent of the command handler that emitted the
    event, so a slow audit sink cannot delay the HTTP response.
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
        await audit_service.record(event)

    @bus.subscribe(MealEntryUpdatedEvent)
    async def on_meal_entry_updated(event: MealEntryUpdatedEvent) -> None:
        logger.info(
            "Nutrition | MealEntryUpdated user_id=%d meal_entry_id=%d target_date=%s",
            event.user_id,
            event.meal_entry_id,
            event.target_date,
        )
        await audit_service.record(event)

    @bus.subscribe(MealEntryDeletedEvent)
    async def on_meal_entry_deleted(event: MealEntryDeletedEvent) -> None:
        logger.info(
            "Nutrition | MealEntryDeleted user_id=%d meal_entry_id=%d target_date=%s",
            event.user_id,
            event.meal_entry_id,
            event.target_date,
        )
        await audit_service.record(event)

    @bus.subscribe(DailyDiaryUpdatedEvent)
    async def on_daily_diary_updated(event: DailyDiaryUpdatedEvent) -> None:
        logger.info(
            "Nutrition | DailyDiaryUpdated user_id=%d diary_id=%d target_date=%s",
            event.user_id,
            event.diary_id,
            event.target_date,
        )
        await audit_service.record(event)
