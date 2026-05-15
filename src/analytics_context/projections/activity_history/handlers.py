import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.analytics_context.projections.activity_history.orm import ActivityHistoryEntry
from src.core_context.activity.contracts.events import WorkoutCompleted
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)

_session_factory: async_sessionmaker[AsyncSession] | None = None


def configure(session_factory: async_sessionmaker[AsyncSession]) -> None:
    global _session_factory
    _session_factory = session_factory


async def project_workout_completed(payload: dict[str, Any]) -> None:
    if _session_factory is None:
        logger.warning("activity_history projection invoked but not configured; dropping")
        return
    event = WorkoutCompleted(**payload)
    async with _session_factory() as session, session.begin():
        session.add(
            ActivityHistoryEntry(
                user_id=event.user_id,
                completed_at=event.occurred_at,
                duration_minutes=event.duration_minutes,
                total_volume_kg=event.total_volume_kg,
            )
        )


PROJECTION_HANDLERS = [
    (WorkoutCompleted, "project_activity_history_workout_completed", project_workout_completed),
]


def register_projection_handlers(bus: IEventBus) -> None:
    for event_type, task_name, handler_fn in PROJECTION_HANDLERS:
        bus.subscribe(event_type, mode="async", task_name=task_name)(handler_fn)
