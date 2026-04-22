from src.nutrition.application.read_models import MacroTotalsReadModel
from src.nutrition.domain.errors import NutritionProfileNotFoundError
from src.nutrition.domain.interfaces import INutritionUnitOfWork
from src.nutrition.domain.models import NutritionProfileDomain


async def require_profile(uow: INutritionUnitOfWork, user_id: int) -> NutritionProfileDomain:
    profile = await uow.repo.get_profile(user_id)
    if profile is None:
        raise NutritionProfileNotFoundError(user_id)
    return profile


def to_macro_read_model(macro) -> MacroTotalsReadModel:
    return MacroTotalsReadModel(
        calories=round(macro.calories, 2),
        protein_g=round(macro.protein_g, 2),
        fat_g=round(macro.fat_g, 2),
        carbs_g=round(macro.carbs_g, 2),
    )
