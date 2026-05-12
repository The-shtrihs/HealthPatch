"""XP calculation logic for nutrition domain activities."""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.nutrition import DailyDiary, MealEntry


@dataclass(frozen=True)
class NutritionRewards:
    """Reward details for nutrition activities."""
    total_xp: int
    is_daily_quest_completed: bool = False  # 3 meal entries in a day


# XP constants
_XP_MEAL_ENTRY: int = 10  # Single meal entry
_XP_DAILY_QUEST_BONUS: int = 30  # Bonus for 3rd meal entry (total = 40)
_XP_DAILY_CALORIE_NORM: int = 50  # Achieving daily calorie goal


async def count_meal_entries_for_day(session: AsyncSession, user_id: int, target_date: date) -> int:
    """Count meal entries logged by user on a specific day."""
    stmt = (
        select(func.count(MealEntry.id))
        .select_from(MealEntry)
        .join(DailyDiary, MealEntry.diary_id == DailyDiary.id)
        .where(DailyDiary.user_id == user_id)
        .where(DailyDiary.target_date == target_date)
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


def calculate_meal_entry_xp(meal_entry_count: int) -> NutritionRewards:
    """
    Calculate XP for adding a meal entry.

    - Single entry: 10 XP
    - 3rd entry in a day (daily quest): +30 bonus → total 40 XP for the 3rd entry

    Args:
        meal_entry_count: Total meal entries for the day after adding the new one

    Returns:
        NutritionRewards with base XP and quest completion status
    """
    if meal_entry_count < 0:
        raise ValueError("meal_entry_count cannot be negative")

    is_daily_quest = meal_entry_count >= 3
    bonus_xp = _XP_DAILY_QUEST_BONUS if is_daily_quest else 0

    return NutritionRewards(
        total_xp=_XP_MEAL_ENTRY + bonus_xp,
        is_daily_quest_completed=is_daily_quest,
    )


def calculate_calorie_norm_xp() -> NutritionRewards:
    """
    Calculate XP for achieving daily calorie goal.

    Returns:
        NutritionRewards with fixed XP for calorie goal achievement
    """
    return NutritionRewards(
        total_xp=_XP_DAILY_CALORIE_NORM,
        is_daily_quest_completed=False,
    )


def calculate_meal_update_xp() -> NutritionRewards:
    """
    Calculate XP for updating a meal entry.

    Returns:
        NutritionRewards with small XP amount for updates
    """
    return NutritionRewards(
        total_xp=5,
        is_daily_quest_completed=False,
    )
