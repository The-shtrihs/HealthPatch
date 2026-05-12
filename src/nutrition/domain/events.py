from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MealEntryAddedEvent:
    user_id: int
    diary_id: int
    meal_entry_id: int
    food_id: int
    meal_type: str
    weight_grams: float
    target_date: date


@dataclass(frozen=True)
class MealEntryUpdatedEvent:
    user_id: int
    meal_entry_id: int
    food_id: int
    meal_type: str
    weight_grams: float
    target_date: date


@dataclass(frozen=True)
class MealEntryDeletedEvent:
    user_id: int
    meal_entry_id: int
    target_date: date


@dataclass(frozen=True)
class DailyDiaryUpdatedEvent:
    user_id: int
    diary_id: int
    target_date: date
    water_ml: int | None
    notes: str | None

@dataclass(frozen=True)
class DailyNormAchievedEvent:
    user_id: int
    diary_id: int
    target_date: date


NutritionEvent = MealEntryAddedEvent | MealEntryUpdatedEvent | MealEntryDeletedEvent | DailyDiaryUpdatedEvent | DailyNormAchievedEvent
