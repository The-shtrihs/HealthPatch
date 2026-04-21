from dataclasses import dataclass
from datetime import date


@dataclass
class AddMealEntryCommand:
    user_id: int
    food_id: int
    meal_type: str
    weight_grams: float
    target_date: date | None = None


@dataclass
class DeleteMealEntryCommand:
    user_id: int
    meal_entry_id: int


@dataclass
class UpdateDailyDiaryCommand:
    user_id: int
    target_date: date
    water_ml: int | None
    notes: str | None
