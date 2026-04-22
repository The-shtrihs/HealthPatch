from dataclasses import dataclass
from datetime import date


@dataclass
class GetDailyNormQuery:
    user_id: int


@dataclass
class GetDayOverviewQuery:
    user_id: int
    target_date: date
