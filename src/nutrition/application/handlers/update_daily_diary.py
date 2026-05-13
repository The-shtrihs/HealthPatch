from src.nutrition.application.commands import UpdateDailyDiaryCommand
from src.nutrition.domain.events import DailyDiaryUpdatedEvent
from src.nutrition.domain.interfaces import INutritionUnitOfWork
from src.shared.application.dispatcher import dispatch_domain_events
from src.shared.infrastructure.event_bus_interface import IEventBus


class UpdateDailyDiaryCommandHandler:
    def __init__(self, uow: INutritionUnitOfWork, bus: IEventBus):
        self._uow = uow
        self._bus = bus

    async def handle(self, command: UpdateDailyDiaryCommand) -> int:
        async with self._uow:
            updated = await self._uow.repo.update_daily_diary(
                user_id=command.user_id,
                target_date=command.target_date,
                water_ml=command.water_ml,
                notes=command.notes,
            )
            diary_id = int(updated["id"] if isinstance(updated, dict) else updated.id)
            self._uow.events.append(
                DailyDiaryUpdatedEvent(
                    user_id=command.user_id,
                    diary_id=diary_id,
                    target_date=command.target_date,
                    water_ml=command.water_ml,
                    notes=command.notes,
                )
            )
        await dispatch_domain_events(self._uow, self._bus)
        return diary_id
