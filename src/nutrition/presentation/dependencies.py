from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.nutrition.application.use_cases import NutritionUseCases
from src.nutrition.infrastructure.repositories import SqlAlchemyNutritionUnitOfWork


async def get_nutrition_use_cases(db: AsyncSession = Depends(get_session)) -> NutritionUseCases:
    return NutritionUseCases(SqlAlchemyNutritionUnitOfWork(db))
