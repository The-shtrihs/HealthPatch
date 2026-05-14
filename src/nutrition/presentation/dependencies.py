from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.dependencies import get_event_bus
from src.nutrition.application.audit_service import INutritionAuditService
from src.nutrition.application.handlers.add_meal_entry import AddMealEntryCommandHandler
from src.nutrition.application.handlers.delete_meal_entry import DeleteMealEntryCommandHandler
from src.nutrition.application.handlers.get_daily_norm import GetDailyNormQueryHandler
from src.nutrition.application.handlers.get_day_overview import GetDayOverviewQueryHandler
from src.nutrition.application.handlers.update_daily_diary import UpdateDailyDiaryCommandHandler
from src.nutrition.application.handlers.update_meal_entry import UpdateMealEntryCommandHandler
from src.nutrition.infrastructure.audit_service import LoggingNutritionAuditService
from src.nutrition.infrastructure.read_repository import SqlAlchemyNutritionReadRepository
from src.nutrition.infrastructure.repositories import SqlAlchemyNutritionUnitOfWork
from src.shared.infrastructure.event_bus_interface import IEventBus


async def get_nutrition_uow(db: AsyncSession = Depends(get_session)) -> SqlAlchemyNutritionUnitOfWork:
    return SqlAlchemyNutritionUnitOfWork(db)


async def get_nutrition_read_repo(db: AsyncSession = Depends(get_session)) -> SqlAlchemyNutritionReadRepository:
    return SqlAlchemyNutritionReadRepository(db)


async def get_get_daily_norm_handler(
    read_repo: SqlAlchemyNutritionReadRepository = Depends(get_nutrition_read_repo),
) -> GetDailyNormQueryHandler:
    return GetDailyNormQueryHandler(read_repo)


async def get_get_day_overview_handler(
    read_repo: SqlAlchemyNutritionReadRepository = Depends(get_nutrition_read_repo),
) -> GetDayOverviewQueryHandler:
    return GetDayOverviewQueryHandler(read_repo)


async def get_nutrition_audit_service() -> INutritionAuditService:
    return LoggingNutritionAuditService()


async def get_add_meal_entry_handler(
    uow: SqlAlchemyNutritionUnitOfWork = Depends(get_nutrition_uow),
    bus: IEventBus = Depends(get_event_bus),
    audit_service: INutritionAuditService = Depends(get_nutrition_audit_service),
) -> AddMealEntryCommandHandler:
    return AddMealEntryCommandHandler(uow, bus, audit_service)


async def get_delete_meal_entry_handler(
    uow: SqlAlchemyNutritionUnitOfWork = Depends(get_nutrition_uow),
    bus: IEventBus = Depends(get_event_bus),
) -> DeleteMealEntryCommandHandler:
    return DeleteMealEntryCommandHandler(uow, bus)


async def get_update_daily_diary_handler(
    uow: SqlAlchemyNutritionUnitOfWork = Depends(get_nutrition_uow),
    bus: IEventBus = Depends(get_event_bus),
) -> UpdateDailyDiaryCommandHandler:
    return UpdateDailyDiaryCommandHandler(uow, bus)


async def get_update_meal_entry_handler(
    uow: SqlAlchemyNutritionUnitOfWork = Depends(get_nutrition_uow),
    bus: IEventBus = Depends(get_event_bus),
) -> UpdateMealEntryCommandHandler:
    return UpdateMealEntryCommandHandler(uow, bus)
