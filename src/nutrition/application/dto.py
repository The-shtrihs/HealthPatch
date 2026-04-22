from dataclasses import dataclass
from datetime import date


@dataclass
class MacroTotalsDto:
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float


@dataclass
class DayOverviewDto:
    target_date: date
    norm: MacroTotalsDto
    consumed: MacroTotalsDto
    remaining: MacroTotalsDto


@dataclass
class GetDayOverviewQuery:
    user_id: int
    target_date: date


@dataclass
class AddMealEntryCommand:
    user_id: int
    food_id: int
    meal_type: str
    weight_grams: float
    target_date: date | None = None


@dataclass
class AddMealEntryResult:
    meal_entry_id: int
    target_date: date
    remaining: MacroTotalsDto


@dataclass
class DeleteMealEntryCommand:
    user_id: int
    meal_entry_id: int


@dataclass
class DeleteMealEntryResult:
    deleted_meal_entry_id: int
    target_date: date
    remaining: MacroTotalsDto


@dataclass
class UpdateDailyDiaryCommand:
    user_id: int
    target_date: date
    water_ml: int | None
    notes: str | None


@dataclass
class UpdateDailyDiaryResult:
    id: int
    user_id: int
    target_date: date
    water_ml: int
    notes: str | None
