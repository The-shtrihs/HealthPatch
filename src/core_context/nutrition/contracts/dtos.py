from datetime import date

from pydantic import BaseModel, ConfigDict


class MealEntryDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    entry_id: int
    user_id: int
    consumed_on: date
    calories: float
    proteins_g: float
    fats_g: float
    carbs_g: float


class DailyTotalsDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    day: date
    calories: float = 0.0
    proteins_g: float = 0.0
    fats_g: float = 0.0
    carbs_g: float = 0.0
