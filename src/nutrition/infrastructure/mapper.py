from typing import Any

from src.models.user import UserProfile
from src.nutrition.domain.models import MacroTotalsDomain, NutritionProfileDomain
from src.user.domain.models import FitnessGoal, Gender


def orm_to_nutrition_profile(profile: UserProfile | None) -> NutritionProfileDomain | None:
    if profile is None:
        return None

    return NutritionProfileDomain(
        age=profile.age,
        weight=profile.weight,
        height=profile.height,
        gender=Gender(str(profile.gender)) if profile.gender is not None else None,
        fitness_goal=FitnessGoal(str(profile.fitness_goal)) if profile.fitness_goal is not None else None,
    )


def to_macro_totals(data: Any) -> MacroTotalsDomain:
    if isinstance(data, dict):
        return MacroTotalsDomain(
            calories=float(data["calories"]),
            protein_g=float(data["protein_g"]),
            fat_g=float(data["fat_g"]),
            carbs_g=float(data["carbs_g"]),
        )

    return MacroTotalsDomain(
        calories=float(data.calories),
        protein_g=float(data.protein_g),
        fat_g=float(data.fat_g),
        carbs_g=float(data.carbs_g),
    )


def diary_to_dict(diary: Any) -> dict[str, Any]:
    return {
        "id": diary.id,
        "user_id": diary.user_id,
        "target_date": diary.target_date,
        "water_ml": diary.water_ml,
        "notes": diary.notes,
    }
