from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.activity.domain.events import WorkoutCompletedEvent
from src.gamification.domain.xp_calculator import calculate_workout_rewards
from src.gamification.infrastructure.unit_of_work import GamificationUnitOfWork
from src.models.gamification import GamificationProfile
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


def register_gamification_handlers(
    bus: IEventBus,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:

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
