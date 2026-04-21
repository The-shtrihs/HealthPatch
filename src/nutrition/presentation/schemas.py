from datetime import date

from pydantic import BaseModel, Field


class DailyNormResponse(BaseModel):
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float


class DayOverviewResponse(BaseModel):
    target_date: date
    norm: DailyNormResponse
    consumed: DailyNormResponse
    remaining: DailyNormResponse


class AddMealEntryRequest(BaseModel):
    food_id: int = Field(gt=0)
    meal_type: str = Field(min_length=1, max_length=20)
    weight_grams: float = Field(gt=0)
    target_date: date | None = None


class AddMealEntryResponse(BaseModel):
    meal_entry_id: int


class UpdateDailyDiaryRequest(BaseModel):
    target_date: date
    water_ml: int | None = Field(default=None, ge=0)
    notes: str | None = None


class UpdateDailyDiaryResponse(BaseModel):
    id: int


class DeleteMealEntryResponse(BaseModel):
    deleted_meal_entry_id: int
