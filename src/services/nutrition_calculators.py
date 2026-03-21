from typing import Protocol

from src.core.exceptions import BadRequestError
from src.models.user import FitnessGoal, Gender, UserProfile

KCAL_PER_GRAM_PROTEIN = 4.0
KCAL_PER_GRAM_CARBS = 4.0
KCAL_PER_GRAM_FAT = 9.0

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
}

ACTIVITY_BY_GOAL = {
    FitnessGoal.WEIGHT_LOSS: ACTIVITY_MULTIPLIERS["lightly_active"],
    FitnessGoal.MUSCLE_GAIN: ACTIVITY_MULTIPLIERS["moderately_active"],
    FitnessGoal.STRENGTH_BUILDING: ACTIVITY_MULTIPLIERS["moderately_active"],
    FitnessGoal.ENDURANCE: ACTIVITY_MULTIPLIERS["very_active"],
}
DEFAULT_ACTIVITY_MULTIPLIER = ACTIVITY_MULTIPLIERS["moderately_active"]


class GoalCalculator(Protocol):
    def calories(self, profile: UserProfile) -> float: ...

    def macros(self, profile: UserProfile, calories: float) -> tuple[float, float, float]: ...


class WeightLossCalculator:
    def calories(self, profile: UserProfile) -> float:
        tdee = _calculate_tdee(profile)
        return tdee * 0.825

    def macros(self, profile: UserProfile, calories: float) -> tuple[float, float, float]:
        protein_g = profile.weight * 2.1
        fat_g = (calories * 0.225) / KCAL_PER_GRAM_FAT
        carbs_g = _carbs_from_remaining_calories(calories, protein_g, fat_g)
        return protein_g, fat_g, carbs_g


class MuscleGainCalculator:
    def calories(self, profile: UserProfile) -> float:
        tdee = _calculate_tdee(profile)
        return tdee * 1.125

    def macros(self, profile: UserProfile, calories: float) -> tuple[float, float, float]:
        protein_g = profile.weight * 1.8
        fat_g = (calories * 0.275) / KCAL_PER_GRAM_FAT
        carbs_g = _carbs_from_remaining_calories(calories, protein_g, fat_g)
        return protein_g, fat_g, carbs_g


class StrengthBuildingCalculator:
    def calories(self, profile: UserProfile) -> float:
        tdee = _calculate_tdee(profile)
        return tdee * 1.03

    def macros(self, profile: UserProfile, calories: float) -> tuple[float, float, float]:
        protein_g = profile.weight * 1.8
        fat_g = (calories * 0.275) / KCAL_PER_GRAM_FAT
        carbs_g = _carbs_from_remaining_calories(calories, protein_g, fat_g)
        return protein_g, fat_g, carbs_g


class EnduranceCalculator:
    def calories(self, profile: UserProfile) -> float:
        tdee = _calculate_tdee(profile)
        return tdee * 1.08

    def macros(self, profile: UserProfile, calories: float) -> tuple[float, float, float]:
        protein_g = profile.weight * 1.35
        fat_g = (calories * 0.25) / KCAL_PER_GRAM_FAT
        carbs_g = _carbs_from_remaining_calories(calories, protein_g, fat_g)
        return protein_g, fat_g, carbs_g


CALCULATORS: dict[FitnessGoal, GoalCalculator] = {
    FitnessGoal.WEIGHT_LOSS: WeightLossCalculator(),
    FitnessGoal.MUSCLE_GAIN: MuscleGainCalculator(),
    FitnessGoal.STRENGTH_BUILDING: StrengthBuildingCalculator(),
    FitnessGoal.ENDURANCE: EnduranceCalculator(),
}


def calculate_daily_norm(profile: UserProfile) -> dict[str, float]:
    goal = profile.fitness_goal
    if goal is None:
        raise BadRequestError(message="Fitness goal is required for nutrition calculations")

    calculator = CALCULATORS.get(goal)
    if calculator is None:
        raise BadRequestError(message=f"Unsupported fitness goal: {goal}")

    calories = calculator.calories(profile)
    protein_g, fat_g, carbs_g = calculator.macros(profile, calories)

    return {
        "calories": calories,
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
    }


def _calculate_bmr(profile: UserProfile) -> float:
    if profile.gender == Gender.MALE:
        gender_constant = 5.0
    elif profile.gender == Gender.FEMALE:
        gender_constant = -161.0
    else:
        raise BadRequestError(message="Unsupported gender for BMR calculation")

    return (10.0 * profile.weight) + (6.25 * profile.height) - (5.0 * profile.age) + gender_constant


def _resolve_activity_multiplier(profile: UserProfile) -> float:
    activity_level = getattr(profile, "activity_level", None)
    if activity_level is None:
        if profile.fitness_goal is not None:
            return ACTIVITY_BY_GOAL.get(profile.fitness_goal, DEFAULT_ACTIVITY_MULTIPLIER)
        return DEFAULT_ACTIVITY_MULTIPLIER

    key = str(activity_level).strip().lower()
    multiplier = ACTIVITY_MULTIPLIERS.get(key)
    if multiplier is None:
        raise BadRequestError(message="Unsupported activity level. Use one of: sedentary, lightly_active, moderately_active, very_active")
    return multiplier


def _calculate_tdee(profile: UserProfile) -> float:
    bmr = _calculate_bmr(profile)
    return bmr * _resolve_activity_multiplier(profile)


def _carbs_from_remaining_calories(calories: float, protein_g: float, fat_g: float) -> float:
    used_calories = (protein_g * KCAL_PER_GRAM_PROTEIN) + (fat_g * KCAL_PER_GRAM_FAT)
    remaining_calories = max(0.0, calories - used_calories)
    return remaining_calories / KCAL_PER_GRAM_CARBS
