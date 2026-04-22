from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.nutrition.application.handlers.add_meal_entry import AddMealEntryCommandHandler
from src.nutrition.application.handlers.delete_meal_entry import DeleteMealEntryCommandHandler
from src.nutrition.application.handlers.get_daily_norm import GetDailyNormQueryHandler
from src.nutrition.application.handlers.get_day_overview import GetDayOverviewQueryHandler
from src.nutrition.application.handlers.update_daily_diary import UpdateDailyDiaryCommandHandler
from src.nutrition.infrastructure.repositories import SqlAlchemyNutritionUnitOfWork


async def get_nutrition_uow(db: AsyncSession = Depends(get_session)) -> SqlAlchemyNutritionUnitOfWork:
    return SqlAlchemyNutritionUnitOfWork(db)


async def get_get_daily_norm_handler(
    uow: SqlAlchemyNutritionUnitOfWork = Depends(get_nutrition_uow),
) -> GetDailyNormQueryHandler:
    return GetDailyNormQueryHandler(uow)


async def get_get_day_overview_handler(
    uow: SqlAlchemyNutritionUnitOfWork = Depends(get_nutrition_uow),
) -> GetDayOverviewQueryHandler:
    return GetDayOverviewQueryHandler(uow)


async def get_add_meal_entry_handler(
    uow: SqlAlchemyNutritionUnitOfWork = Depends(get_nutrition_uow),
) -> AddMealEntryCommandHandler:
    return AddMealEntryCommandHandler(uow)


async def get_delete_meal_entry_handler(
    uow: SqlAlchemyNutritionUnitOfWork = Depends(get_nutrition_uow),
) -> DeleteMealEntryCommandHandler:
    return DeleteMealEntryCommandHandler(uow)


async def get_update_daily_diary_handler(
    uow: SqlAlchemyNutritionUnitOfWork = Depends(get_nutrition_uow),
) -> UpdateDailyDiaryCommandHandler:
    return UpdateDailyDiaryCommandHandler(uow)
