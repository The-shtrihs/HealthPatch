import logging
from datetime import UTC, datetime

from src.nutrition.application.audit_service import INutritionAuditService
from src.nutrition.application.commands import AddMealEntryCommand
from src.nutrition.domain.events import DailyNormAchievedEvent, MealEntryAddedEvent
from src.nutrition.domain.interfaces import INutritionUnitOfWork
from src.nutrition.domain.models import MealEntryCreateDomain
from src.shared.application.dispatcher import dispatch_domain_events
from src.shared.infrastructure.event_bus_interface import IEventBus

from ._shared import require_profile

logger = logging.getLogger(__name__)


class AddMealEntryCommandHandler:
    def __init__(
        self,
        uow: INutritionUnitOfWork,
        bus: IEventBus,
        audit_service: INutritionAuditService,
    ):
        self._uow = uow
        self._bus = bus
        self._audit_service = audit_service

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
            meal_added_event = MealEntryAddedEvent(
                user_id=command.user_id,
                diary_id=diary_id,
                meal_entry_id=meal_entry_id,
                food_id=create.food_id,
                meal_type=meal_type,
                weight_grams=create.weight_grams,
                target_date=day,
            )
            self._uow.events.append(meal_added_event)
            try:
                totals = await self._uow.repo.get_day_consumed_totals(command.user_id, day)
                user_profile = await self._uow.repo.get_profile(command.user_id)
                if user_profile is not None:
                    from src.nutrition.domain.calculations import calculate_daily_norm

                    norm = calculate_daily_norm(user_profile)
                    if float(totals.calories) >= norm.calories:
                        self._uow.events.append(
                            DailyNormAchievedEvent(
                                user_id=command.user_id,
                                diary_id=diary_id,
                                target_date=day,
                            )
                        )
            except Exception:
                pass

        # Synchronous audit: direct call to the audit service in the same
        # thread, right after the diary write commits. Audit is auxiliary —
        # if it fails we log and move on so the user still gets a 201 with
        # the new meal_entry_id.
        try:
            await self._audit_service.record(meal_added_event)
        except Exception:
            logger.exception("Audit recording failed for MealEntryAddedEvent meal_entry_id=%s", meal_entry_id)

        await dispatch_domain_events(self._uow, self._bus)
        return meal_entry_id
