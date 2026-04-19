from typing import Protocol

from src.nutrition.domain.errors import (
	UnsupportedActivityLevelError,
	UnsupportedFitnessGoalError,
	UnsupportedGenderError,
)
from src.nutrition.domain.models import MacroTotalsDomain, NutritionProfileDomain
from src.user.domain.models import FitnessGoal, Gender

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
	def calories(self, profile: NutritionProfileDomain) -> float: ...

	def macros(self, profile: NutritionProfileDomain, calories: float) -> tuple[float, float, float]: ...


class WeightLossCalculator:
	def calories(self, profile: NutritionProfileDomain) -> float:
		tdee = calculate_tdee(profile)
		return tdee * 0.825

	def macros(self, profile: NutritionProfileDomain, calories: float) -> tuple[float, float, float]:
		protein_g = profile.weight * 2.1
		fat_g = (calories * 0.225) / KCAL_PER_GRAM_FAT
		carbs_g = carbs_from_remaining_calories(calories, protein_g, fat_g)
		return protein_g, fat_g, carbs_g


class MuscleGainCalculator:
	def calories(self, profile: NutritionProfileDomain) -> float:
		tdee = calculate_tdee(profile)
		return tdee * 1.125

	def macros(self, profile: NutritionProfileDomain, calories: float) -> tuple[float, float, float]:
		protein_g = profile.weight * 1.8
		fat_g = (calories * 0.275) / KCAL_PER_GRAM_FAT
		carbs_g = carbs_from_remaining_calories(calories, protein_g, fat_g)
		return protein_g, fat_g, carbs_g


class StrengthBuildingCalculator:
	def calories(self, profile: NutritionProfileDomain) -> float:
		tdee = calculate_tdee(profile)
		return tdee * 1.03

	def macros(self, profile: NutritionProfileDomain, calories: float) -> tuple[float, float, float]:
		protein_g = profile.weight * 1.8
		fat_g = (calories * 0.275) / KCAL_PER_GRAM_FAT
		carbs_g = carbs_from_remaining_calories(calories, protein_g, fat_g)
		return protein_g, fat_g, carbs_g


class EnduranceCalculator:
	def calories(self, profile: NutritionProfileDomain) -> float:
		tdee = calculate_tdee(profile)
		return tdee * 1.08

	def macros(self, profile: NutritionProfileDomain, calories: float) -> tuple[float, float, float]:
		protein_g = profile.weight * 1.35
		fat_g = (calories * 0.25) / KCAL_PER_GRAM_FAT
		carbs_g = carbs_from_remaining_calories(calories, protein_g, fat_g)
		return protein_g, fat_g, carbs_g


CALCULATORS: dict[FitnessGoal, GoalCalculator] = {
	FitnessGoal.WEIGHT_LOSS: WeightLossCalculator(),
	FitnessGoal.MUSCLE_GAIN: MuscleGainCalculator(),
	FitnessGoal.STRENGTH_BUILDING: StrengthBuildingCalculator(),
	FitnessGoal.ENDURANCE: EnduranceCalculator(),
}


def calculate_daily_norm(profile: NutritionProfileDomain) -> MacroTotalsDomain:
	profile.ensure_complete()

	calculator = CALCULATORS.get(profile.fitness_goal)
	if calculator is None:
		raise UnsupportedFitnessGoalError(str(profile.fitness_goal))

	calories = calculator.calories(profile)
	protein_g, fat_g, carbs_g = calculator.macros(profile, calories)
	return MacroTotalsDomain(
		calories=calories,
		protein_g=protein_g,
		fat_g=fat_g,
		carbs_g=carbs_g,
	)


def calculate_bmr(profile: NutritionProfileDomain) -> float:
	if profile.gender == Gender.MALE:
		gender_constant = 5.0
	elif profile.gender == Gender.FEMALE:
		gender_constant = -161.0
	else:
		raise UnsupportedGenderError()

	return (10.0 * profile.weight) + (6.25 * profile.height) - (5.0 * profile.age) + gender_constant


def resolve_activity_multiplier(profile: NutritionProfileDomain) -> float:
	if profile.activity_level is None:
		if profile.fitness_goal is not None:
			return ACTIVITY_BY_GOAL.get(profile.fitness_goal, DEFAULT_ACTIVITY_MULTIPLIER)
		return DEFAULT_ACTIVITY_MULTIPLIER

	key = profile.activity_level.strip().lower()
	multiplier = ACTIVITY_MULTIPLIERS.get(key)
	if multiplier is None:
		raise UnsupportedActivityLevelError()
	return multiplier


def calculate_tdee(profile: NutritionProfileDomain) -> float:
	bmr = calculate_bmr(profile)
	return bmr * resolve_activity_multiplier(profile)


def carbs_from_remaining_calories(calories: float, protein_g: float, fat_g: float) -> float:
	used_calories = (protein_g * KCAL_PER_GRAM_PROTEIN) + (fat_g * KCAL_PER_GRAM_FAT)
	remaining_calories = max(0.0, calories - used_calories)
	return remaining_calories / KCAL_PER_GRAM_CARBS
