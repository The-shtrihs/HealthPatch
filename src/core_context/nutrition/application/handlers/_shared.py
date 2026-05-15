from src.core_context.nutrition.application.read_models import MacroTotalsReadModel
from src.core_context.nutrition.domain.errors import NutritionProfileNotFoundError
from src.core_context.nutrition.domain.interfaces import INutritionReadRepository
from src.core_context.nutrition.domain.models import NutritionProfileDomain


async def require_profile(repo: INutritionReadRepository, user_id: int) -> NutritionProfileDomain:
    profile = await repo.get_profile(user_id)
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
