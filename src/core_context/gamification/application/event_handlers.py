from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core_context.activity.contracts.events import WorkoutCompleted
from src.core_context.gamification.acl.translators import (
    XpAwardCommand,
    from_daily_norm_achieved,
    from_meal_entry_added,
    from_meal_entry_updated,
    from_workout_completed,
)
from src.core_context.gamification.domain.xp_calculator import (
    calculate_daily_norm_xp,
    calculate_meal_add_xp,
    calculate_meal_update_xp,
    calculate_workout_rewards,
)
from src.core_context.gamification.infrastructure.unit_of_work import GamificationUnitOfWork
from src.core_context.nutrition.contracts.events import (
    DailyNormAchieved,
    MealEntryAdded,
    MealEntryUpdated,
)
from src.core_context.nutrition.contracts.ports import IMealEntryQueries
from src.shared.infrastructure.daily_claim_store import DailyClaimStore, RedisDailyClaimStore
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


def register_gamification_handlers(
    bus: IEventBus,
    session_factory: async_sessionmaker[AsyncSession],
    meal_entry_queries: IMealEntryQueries,
    daily_claim_store: DailyClaimStore | None = None,
) -> None:
    claim_store = daily_claim_store or RedisDailyClaimStore()

    @bus.subscribe(MealEntryAdded, mode="sync")
    async def on_meal_entry_added(event: MealEntryAdded) -> None:
        cmd = from_meal_entry_added(event)
        meal_entry_count = await meal_entry_queries.count_for_day(cmd.user_id, event.consumed_on)
        async with session_factory() as session, GamificationUnitOfWork(session) as uow:
            await uow.profiles.ensure_profile(cmd.user_id)
            await uow.profiles.award_xp(cmd.user_id, calculate_meal_add_xp(meal_entry_count))

    @bus.subscribe(MealEntryUpdated, mode="sync")
    async def on_meal_entry_updated(event: MealEntryUpdated) -> None:
        cmd = from_meal_entry_updated(event)
        async with session_factory() as session, GamificationUnitOfWork(session) as uow:
            await uow.profiles.ensure_profile(cmd.user_id)
            await uow.profiles.award_xp(cmd.user_id, calculate_meal_update_xp())

    @bus.subscribe(DailyNormAchieved, mode="sync")
    async def on_daily_norm_achieved(event: DailyNormAchieved) -> None:
        cmd = from_daily_norm_achieved(event)
        async with session_factory() as session, GamificationUnitOfWork(session) as uow:
            await uow.profiles.ensure_profile(cmd.user_id)

            try:
                claimed = await claim_store.try_claim(cmd.user_id, event.day)
            except RuntimeError:
                return
            except Exception:
                logger.exception("Daily claim store error while setting daily-norm claim key")
                return

            if claimed:
                await uow.profiles.award_xp(cmd.user_id, calculate_daily_norm_xp())

    @bus.subscribe(WorkoutCompleted, mode="sync")
    async def on_workout_completed(event: WorkoutCompleted) -> None:
        cmd: XpAwardCommand = from_workout_completed(event)
        async with session_factory() as session, GamificationUnitOfWork(session) as uow:
            await uow.profiles.ensure_profile(cmd.user_id)

            rewards = calculate_workout_rewards(
                duration_minutes=cmd.duration_minutes or 0,
                volume_kg=cmd.volume_kg or 0.0,
            )

            await uow.profiles.award_xp(cmd.user_id, rewards.total_xp)
