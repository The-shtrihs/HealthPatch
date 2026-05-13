import pytest

from src.gamification.domain.xp_calculator import (
    calculate_daily_norm_xp,
    calculate_meal_add_xp,
    calculate_meal_update_xp,
    calculate_workout_rewards,
)


def test_calculate_meal_add_xp_base_award() -> None:
    assert calculate_meal_add_xp(1) == 10


def test_calculate_meal_add_xp_third_meal_bonus() -> None:
    assert calculate_meal_add_xp(3) == 40


def test_calculate_meal_add_xp_requires_positive_count() -> None:
    with pytest.raises(ValueError, match="meal_entry_count must be positive"):
        calculate_meal_add_xp(0)


def test_calculate_meal_update_xp() -> None:
    assert calculate_meal_update_xp() == 5


def test_calculate_daily_norm_xp() -> None:
    assert calculate_daily_norm_xp() == 50


def test_calculate_workout_rewards_uses_duration_and_volume() -> None:
    rewards = calculate_workout_rewards(duration_minutes=30, volume_kg=100.0)
    assert rewards.total_xp == 62


def test_calculate_workout_rewards_rejects_negative_duration() -> None:
    with pytest.raises(ValueError, match="duration_minutes cannot be negative"):
        calculate_workout_rewards(duration_minutes=-1, volume_kg=0.0)


def test_calculate_workout_rewards_rejects_negative_volume() -> None:
    with pytest.raises(ValueError, match="volume_kg cannot be negative"):
        calculate_workout_rewards(duration_minutes=10, volume_kg=-0.1)
