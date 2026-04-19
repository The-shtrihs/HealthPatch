from dataclasses import dataclass
from datetime import date

from src.nutrition.domain.errors import IncompleteNutritionProfileError, InvalidMealEntryError
from src.user.domain.models import FitnessGoal, Gender


@dataclass
class NutritionProfileDomain:
    age: int | None
    weight: float | None
    height: float | None
    gender: Gender | None
    fitness_goal: FitnessGoal | None
    activity_level: str | None = None

    def missing_required_fields(self) -> list[str]:
        missing_fields: list[str] = []
        if self.age is None:
            missing_fields.append("age")
        if self.weight is None:
            missing_fields.append("weight")
        if self.height is None:
            missing_fields.append("height")
        if self.gender is None:
            missing_fields.append("gender")
        if self.fitness_goal is None:
            missing_fields.append("fitness_goal")
        return missing_fields

    def ensure_complete(self) -> None:
        missing_fields = self.missing_required_fields()
        if missing_fields:
            raise IncompleteNutritionProfileError(missing_fields)


@dataclass
class MacroTotalsDomain:
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float

    def remaining_after(self, consumed: "MacroTotalsDomain") -> "MacroTotalsDomain":
        return MacroTotalsDomain(
            calories=max(0.0, self.calories - consumed.calories),
            protein_g=max(0.0, self.protein_g - consumed.protein_g),
            fat_g=max(0.0, self.fat_g - consumed.fat_g),
            carbs_g=max(0.0, self.carbs_g - consumed.carbs_g),
        )


@dataclass
class DayOverviewDomain:
    target_date: date
    norm: MacroTotalsDomain
    consumed: MacroTotalsDomain
    remaining: MacroTotalsDomain


@dataclass
class MealEntryCreateDomain:
    food_id: int
    meal_type: str
    weight_grams: float
    target_date: date | None = None

    def normalized_meal_type(self) -> str:
        meal_type = self.meal_type.strip()
        if not meal_type:
            raise InvalidMealEntryError("Meal type is required")
        return meal_type

    def validate(self) -> None:
        if self.food_id <= 0:
            raise InvalidMealEntryError("Food id must be greater than 0")
        if self.weight_grams <= 0:
            raise InvalidMealEntryError("Meal weight must be greater than 0")
        self.normalized_meal_type()
