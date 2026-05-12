from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.activity.domain.events import WorkoutCompletedEvent
from src.gamification.domain.xp_calculator import (
    calculate_daily_norm_xp,
    calculate_meal_add_xp,
    calculate_meal_update_xp,
    calculate_workout_rewards,
)
from src.gamification.infrastructure.unit_of_work import GamificationUnitOfWork
from src.nutrition.domain.events import MealEntryAddedEvent, MealEntryUpdatedEvent, DailyNormAchievedEvent
from src.shared.infrastructure.daily_claim_store import DailyClaimStore, RedisDailyClaimStore
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


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
