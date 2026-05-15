from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class FitnessGoal(StrEnum):
    WEIGHT_LOSS = "weight loss"
    MUSCLE_GAIN = "muscle gain"
    STRENGTH_BUILDING = "strength building"
    ENDURANCE = "endurance"


class NutritionTargetsDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    calories: int | None = None
    proteins_g: float | None = None
    fats_g: float | None = None
    carbs_g: float | None = None


class UserProfileDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    display_name: str | None = None
    gender: Gender | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    fitness_goal: FitnessGoal | None = None
    nutrition_targets: NutritionTargetsDTO | None = None
