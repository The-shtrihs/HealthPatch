from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.activity.domain.events import WorkoutCompletedEvent
from src.gamification.domain.xp_calculator import calculate_workout_rewards
from src.gamification.infrastructure.unit_of_work import GamificationUnitOfWork
from src.models.gamification import GamificationProfile
from src.models.nutrition import DailyDiary, Food, MealEntry
import src.core.redis as redis_module
from datetime import datetime, time, timedelta, timezone
from src.models.user import UserProfile
from src.nutrition.domain.calculations import calculate_daily_norm
from src.nutrition.domain.events import MealEntryAddedEvent, MealEntryUpdatedEvent, DailyNormAchievedEvent
from src.nutrition.domain.models import NutritionProfileDomain
from src.nutrition.domain.xp_calculator import calculate_daily_norm_rewards, calculate_meal_add_rewards, calculate_meal_update_rewards
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


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

            next_midnight = datetime.combine(date_part, time.min, tzinfo=timezone.utc) + timedelta(days=1)
            now = datetime.now(timezone.utc)
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
        profile.total_xp += calculate_daily_norm_rewards().total_xp


def register_gamification_handlers(
    bus: IEventBus,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:

    @bus.subscribe(MealEntryAddedEvent)
    async def on_meal_entry_added(event: MealEntryAddedEvent) -> None:
        logger.info(
            "Gamification ▸ MealEntryAdded user_id=%d meal_entry_id=%d",
            event.user_id,
            event.meal_entry_id,
        )

        async with session_factory() as session:
            async with GamificationUnitOfWork(session) as uow:
                profile = await uow.profiles.get_by_user_id(event.user_id)
                if profile is None:
                    profile = GamificationProfile(user_id=event.user_id)
                    await uow.profiles.add(profile)

                meal_entry_count = await session.scalar(
                    select(func.count(MealEntry.id))
                    .select_from(MealEntry)
                    .join(DailyDiary, MealEntry.daily_diary_id == DailyDiary.id)
                    .where(DailyDiary.user_id == event.user_id)
                    .where(DailyDiary.target_date == event.target_date)
                )
                reward = calculate_meal_add_rewards(int(meal_entry_count or 0))
                profile.total_xp += reward.total_xp

    @bus.subscribe(MealEntryUpdatedEvent)
    async def on_meal_entry_updated(event: MealEntryUpdatedEvent) -> None:
        logger.info(
            "Gamification ▸ MealEntryUpdated user_id=%d meal_entry_id=%d",
            event.user_id,
            event.meal_entry_id,
        )

        async with session_factory() as session:
            async with GamificationUnitOfWork(session) as uow:
                profile = await uow.profiles.get_by_user_id(event.user_id)
                if profile is None:
                    profile = GamificationProfile(user_id=event.user_id)
                    await uow.profiles.add(profile)

                profile.total_xp += calculate_meal_update_rewards().total_xp

    @bus.subscribe(DailyNormAchievedEvent)
    async def on_daily_norm_achieved(event: DailyNormAchievedEvent) -> None:
        logger.info(
            "Gamification ▸ DailyNormAchieved user_id=%d target_date=%s",
            event.user_id,
            event.target_date,
        )

        async with session_factory() as session:
            async with GamificationUnitOfWork(session) as uow:
                profile = await uow.profiles.get_by_user_id(event.user_id)
                if profile is None:
                    profile = GamificationProfile(user_id=event.user_id)
                    await uow.profiles.add(profile)

                try:
                    redis = redis_module.get_redis()
                except RuntimeError:
                    logger.warning("Redis not available for daily-norm claim check; skipping award")
                    return

                key_date = getattr(event.target_date, "isoformat", lambda: str(event.target_date))()
                key = f"daily_norm:{event.user_id}:{key_date}"

                try:
                    try:
                        if hasattr(event.target_date, "date"):
                            date_part = event.target_date.date() if isinstance(event.target_date, datetime) else event.target_date
                        else:
                            date_part = event.target_date

                        next_midnight = datetime.combine(date_part, time.min, tzinfo=timezone.utc) + timedelta(days=1)
                        now = datetime.now(timezone.utc)
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
                    profile.total_xp += calculate_daily_norm_rewards().total_xp

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
                profile = await uow.profiles.get_by_user_id(event.user_id)
                if profile is None:
                    profile = GamificationProfile(user_id=event.user_id)
                    await uow.profiles.add(profile)
                    logger.info("Gamification ▸ created profile user_id=%d", event.user_id)

                rewards = calculate_workout_rewards(
                    duration_minutes=event.duration_minutes,
                    volume_kg=event.volume_kg,
                )

                profile.total_xp += rewards.total_xp

            logger.info(
                "Gamification ▸ user_id=%d +%d XP → total %d XP",
                event.user_id,
                rewards.total_xp,
                profile.total_xp,
            )
