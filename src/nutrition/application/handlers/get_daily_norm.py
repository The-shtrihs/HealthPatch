from src.nutrition.application.queries import GetDailyNormQuery
from src.nutrition.application.read_models import MacroTotalsReadModel
from src.nutrition.domain.calculations import calculate_daily_norm
from src.nutrition.domain.interfaces import INutritionUnitOfWork

from ._shared import require_profile, to_macro_read_model


class GetDailyNormQueryHandler:
    def __init__(self, uow: INutritionUnitOfWork):
        self._uow = uow

    async def handle(self, query: GetDailyNormQuery) -> MacroTotalsReadModel:
        profile = await require_profile(self._uow, query.user_id)
        norm = calculate_daily_norm(profile)
        return to_macro_read_model(norm)
