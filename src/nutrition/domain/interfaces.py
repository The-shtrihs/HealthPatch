from abc import ABC, abstractmethod
from datetime import date

from src.nutrition.domain.models import MacroTotalsDomain, NutritionProfileDomain


class INutritionRepository(ABC):
    @abstractmethod
    async def get_profile(self, user_id: int) -> NutritionProfileDomain | None: ...

    @abstractmethod
    async def get_day_consumed_totals(self, user_id: int, target_date: date) -> MacroTotalsDomain: ...

    @abstractmethod
    async def ensure_daily_diary(self, user_id: int, target_date: date) -> int: ...

    @abstractmethod
    async def add_meal_entry(self, diary_id: int, food_id: int, meal_type: str, weight_grams: float) -> int: ...

    @abstractmethod
    async def get_user_meal_entry_target_date(self, user_id: int, meal_entry_id: int) -> date | None: ...

    @abstractmethod
    async def delete_meal_entry(self, meal_entry_id: int) -> None: ...

    @abstractmethod
    async def update_daily_diary(self, user_id: int, target_date: date, water_ml: int | None, notes: str | None) -> dict: ...


class INutritionUnitOfWork(ABC):
    repo: INutritionRepository

    @abstractmethod
    async def __aenter__(self): ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb): ...
