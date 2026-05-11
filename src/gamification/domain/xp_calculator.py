from typing import Final

from src.gamification.domain.value_objects import WorkoutRewards

_XP_PER_MINUTE: Final[float] = 2.0
_XP_PER_50KG_VOLUME: Final[float] = 1.0


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
