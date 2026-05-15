from typing import Final

from src.core_context.gamification.domain.value_objects import WorkoutRewards

_XP_PER_MINUTE: Final[float] = 2.0
_XP_PER_50KG_VOLUME: Final[float] = 1.0
_MEAL_ADD_XP: Final[int] = 10
_MEAL_ADD_STREAK_THRESHOLD: Final[int] = 3
_MEAL_ADD_STREAK_BONUS_XP: Final[int] = 30
_MEAL_UPDATE_XP: Final[int] = 5
_DAILY_NORM_XP: Final[int] = 50


def calculate_workout_rewards(
    duration_minutes: int,
    volume_kg: float,
) -> WorkoutRewards:
    if duration_minutes < 0:
        raise ValueError("duration_minutes cannot be negative")
    if volume_kg < 0:
        raise ValueError("volume_kg cannot be negative")

    base_xp = int(duration_minutes * _XP_PER_MINUTE + (volume_kg / 50 * _XP_PER_50KG_VOLUME))

    return WorkoutRewards(
        total_xp=base_xp,
    )


def calculate_meal_add_xp(meal_entry_count: int) -> int:
    if meal_entry_count < 1:
        raise ValueError("meal_entry_count must be positive")

    bonus_xp = _MEAL_ADD_STREAK_BONUS_XP if meal_entry_count == _MEAL_ADD_STREAK_THRESHOLD else 0
    return _MEAL_ADD_XP + bonus_xp


def calculate_meal_update_xp() -> int:
    return _MEAL_UPDATE_XP


def calculate_daily_norm_xp() -> int:
    return _DAILY_NORM_XP
