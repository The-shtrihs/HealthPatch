from src.nutrition.application.commands import UpdateDailyDiaryCommand
from src.nutrition.domain.events import DailyDiaryUpdatedEvent
from src.nutrition.domain.interfaces import INutritionUnitOfWork


class UpdateDailyDiaryCommandHandler:
    def __init__(self, uow: INutritionUnitOfWork):
        self._uow = uow

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
        return diary_id
