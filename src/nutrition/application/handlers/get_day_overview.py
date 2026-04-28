from src.nutrition.application.queries import GetDayOverviewQuery
from src.nutrition.application.read_models import DayOverviewReadModel
from src.nutrition.domain.calculations import calculate_daily_norm
from src.nutrition.domain.interfaces import INutritionReadRepository

from ._shared import require_profile, to_macro_read_model


class GetDayOverviewQueryHandler:
    def __init__(self, read_repo: INutritionReadRepository):
        self._read_repo = read_repo

    async def handle(self, query: GetDayOverviewQuery) -> DayOverviewReadModel:
        profile = await require_profile(self._read_repo, query.user_id)

        norm = calculate_daily_norm(profile)
        consumed = await self._read_repo.get_day_consumed_totals(query.user_id, query.target_date)
        remaining = norm.remaining_after(consumed)

        return DayOverviewReadModel(
            target_date=query.target_date,
            norm=to_macro_read_model(norm),
            consumed=to_macro_read_model(consumed),
            remaining=to_macro_read_model(remaining),
        )
