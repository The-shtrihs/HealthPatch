from __future__ import annotations

import logging
<<<<<<< HEAD
from datetime import datetime
=======
from datetime import UTC, datetime, time, timedelta
>>>>>>> origin/nutrition/xp

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import src.core.redis as redis_module
from src.activity.domain.events import WorkoutCompletedEvent
from src.gamification.domain.xp_calculator import (
    calculate_daily_norm_xp,
    calculate_meal_add_xp,
    calculate_meal_update_xp,
    calculate_workout_rewards,
)
from src.gamification.infrastructure.unit_of_work import GamificationUnitOfWork
<<<<<<< HEAD
from src.nutrition.domain.events import MealEntryAddedEvent, MealEntryUpdatedEvent, DailyNormAchievedEvent
from src.shared.infrastructure.daily_claim_store import DailyClaimStore, RedisDailyClaimStore
=======
from src.models.gamification import GamificationProfile
from src.models.nutrition import DailyDiary, Food, MealEntry
from src.models.user import UserProfile
from src.nutrition.domain.calculations import calculate_daily_norm
from src.nutrition.domain.events import DailyNormAchievedEvent, MealEntryAddedEvent, MealEntryUpdatedEvent
from src.nutrition.domain.models import NutritionProfileDomain
>>>>>>> origin/nutrition/xp
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


<<<<<<< HEAD
=======
async def maybe_award_daily_norm_xp(session: AsyncSession, user_id: int, target_date, profile: GamificationProfile) -> None:
    diary = await session.scalar(
        select(DailyDiary).where(
            DailyDiary.user_id == user_id,
            DailyDiary.target_date == target_date,
        )
    )
    if diary is None:
        return

    user_profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if user_profile is None:
        return

    nutrition_profile = NutritionProfileDomain(
        age=user_profile.age,
        weight=user_profile.weight,
        height=user_profile.height,
        gender=user_profile.gender,
        fitness_goal=user_profile.fitness_goal,
    )

    try:
        norm = calculate_daily_norm(nutrition_profile)
    except Exception:
        return

    consumed = await session.scalar(
        select(
            func.coalesce(
                func.sum(Food.calories_per_100g * (MealEntry.weight_grams / 100.0)),
                0.0,
            )
        )
        .select_from(DailyDiary)
        .join(MealEntry, MealEntry.daily_diary_id == DailyDiary.id)
        .join(Food, Food.id == MealEntry.food_id)
        .where(DailyDiary.user_id == user_id)
        .where(DailyDiary.target_date == target_date)
    )
    calories = float(consumed or 0.0)
    if calories < norm.calories:
        return

    try:
        redis = redis_module.get_redis()
    except RuntimeError:
        logger.warning("Redis not available for daily-norm claim check; skipping award")
        return

    key_date = getattr(target_date, "isoformat", lambda: str(target_date))()
    key = f"daily_norm:{user_id}:{key_date}"

    try:
        try:
            if hasattr(target_date, "date"):
                date_part = target_date.date() if isinstance(target_date, datetime) else target_date
            else:
                date_part = target_date

            next_midnight = datetime.combine(date_part, time.min, tzinfo=UTC) + timedelta(days=1)
            now = datetime.now(UTC)
            expiry_seconds = int((next_midnight - now).total_seconds())
            if expiry_seconds <= 0:
                expiry_seconds = 60 * 60 * 24
        except Exception:
            expiry_seconds = 60 * 60 * 24

        was_set = await redis.set(key, "1", nx=True, ex=expiry_seconds)
    except Exception:
        logger.exception("Redis error while setting daily-norm claim key")
        return

    if was_set:
        profile.total_xp += calculate_daily_norm_xp()


>>>>>>> origin/nutrition/xp
def register_gamification_handlers(
    bus: IEventBus,
    session_factory: async_sessionmaker[AsyncSession],
    daily_claim_store: DailyClaimStore | None = None,
) -> None:
    claim_store = daily_claim_store or RedisDailyClaimStore()

    @bus.subscribe(MealEntryAddedEvent)
    async def on_meal_entry_added(event: MealEntryAddedEvent) -> None:
        logger.info(
            "Gamification ▸ MealEntryAdded user_id=%d meal_entry_id=%d",
            event.user_id,
            event.meal_entry_id,
        )

        async with session_factory() as session:
            async with GamificationUnitOfWork(session) as uow:
                await uow.profiles.ensure_profile(event.user_id)

                meal_entry_count = await uow.profiles.count_meal_entries_for_day(event.user_id, event.target_date)
                await uow.profiles.award_xp(event.user_id, calculate_meal_add_xp(meal_entry_count))

    @bus.subscribe(MealEntryUpdatedEvent)
    async def on_meal_entry_updated(event: MealEntryUpdatedEvent) -> None:
        logger.info(
            "Gamification ▸ MealEntryUpdated user_id=%d meal_entry_id=%d",
            event.user_id,
            event.meal_entry_id,
        )

        async with session_factory() as session:
            async with GamificationUnitOfWork(session) as uow:
                await uow.profiles.ensure_profile(event.user_id)

                await uow.profiles.award_xp(event.user_id, calculate_meal_update_xp())

    @bus.subscribe(DailyNormAchievedEvent)
    async def on_daily_norm_achieved(event: DailyNormAchievedEvent) -> None:
        logger.info(
            "Gamification ▸ DailyNormAchieved user_id=%d target_date=%s",
            event.user_id,
            event.target_date,
        )

        async with session_factory() as session:
            async with GamificationUnitOfWork(session) as uow:
                await uow.profiles.ensure_profile(event.user_id)

                try:
                    claimed = await claim_store.try_claim(event.user_id, event.target_date)
                except RuntimeError:
                    logger.warning("Redis not available for daily-norm claim check; skipping award")
                    return
<<<<<<< HEAD
=======

                key_date = getattr(event.target_date, "isoformat", lambda: str(event.target_date))()
                key = f"daily_norm:{event.user_id}:{key_date}"

                try:
                    try:
                        if hasattr(event.target_date, "date"):
                            date_part = event.target_date.date() if isinstance(event.target_date, datetime) else event.target_date
                        else:
                            date_part = event.target_date

                        next_midnight = datetime.combine(date_part, time.min, tzinfo=UTC) + timedelta(days=1)
                        now = datetime.now(UTC)
                        expiry_seconds = int((next_midnight - now).total_seconds())
                        if expiry_seconds <= 0:
                            expiry_seconds = 60 * 60 * 24
                    except Exception:
                        expiry_seconds = 60 * 60 * 24

                    was_set = await redis.set(key, "1", nx=True, ex=expiry_seconds)
>>>>>>> origin/nutrition/xp
                except Exception:
                    logger.exception("Daily claim store error while setting daily-norm claim key")
                    return

                if claimed:
                    await uow.profiles.award_xp(event.user_id, calculate_daily_norm_xp())

    @bus.subscribe(WorkoutCompletedEvent)
    async def on_workout_completed(event: WorkoutCompletedEvent) -> None:
        logger.info(
            "Gamification ▸ WorkoutCompleted user_id=%d (%d min, %.1f kg)",
            event.user_id,
            event.duration_minutes,
            event.volume_kg,
        )

        async with session_factory() as session:
            async with GamificationUnitOfWork(session) as uow:
                await uow.profiles.ensure_profile(event.user_id)

                rewards = calculate_workout_rewards(
                    duration_minutes=event.duration_minutes,
                    volume_kg=event.volume_kg,
                )

                total_xp = await uow.profiles.award_xp(event.user_id, rewards.total_xp)

            logger.info(
                "Gamification ▸ user_id=%d +%d XP → total %d XP",
                event.user_id,
                rewards.total_xp,
                total_xp,
            )
