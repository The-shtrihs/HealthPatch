from src.nutrition.application.commands import UpdateDailyDiaryCommand
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
        if isinstance(updated, dict):
            return int(updated["id"])
        return int(updated.id)
