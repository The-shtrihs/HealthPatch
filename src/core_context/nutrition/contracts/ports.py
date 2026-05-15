from datetime import date
from typing import Protocol, runtime_checkable

from src.core_context.nutrition.contracts.dtos import DailyTotalsDTO


@runtime_checkable
class IDailyTotalsDirectory(Protocol):
    async def get(self, user_id: int, day: date) -> DailyTotalsDTO | None: ...


@runtime_checkable
class IMealEntryQueries(Protocol):
    async def count_for_day(self, user_id: int, day: date) -> int: ...
