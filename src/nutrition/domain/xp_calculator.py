from dataclasses import dataclass


@dataclass(frozen=True)
class NutritionRewards:
    total_xp: int


def calculate_meal_add_rewards(meal_entry_count: int) -> NutritionRewards:
    if meal_entry_count < 1:
        raise ValueError("meal_entry_count must be positive")

    bonus_xp = 30 if meal_entry_count == 3 else 0
    return NutritionRewards(total_xp=10 + bonus_xp)


def calculate_meal_update_rewards() -> NutritionRewards:
    return NutritionRewards(total_xp=5)


def calculate_daily_norm_rewards() -> NutritionRewards:
    return NutritionRewards(total_xp=50)
