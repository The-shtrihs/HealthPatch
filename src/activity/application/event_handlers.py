from __future__ import annotations

import logging

from src.activity.domain.events import (
    PersonalRecordBeaten,
    WorkoutPlanCreated,
    WorkoutPlanDeleted,
    WorkoutPlanMadePublic,
    WorkoutSessionEnded,
    WorkoutSessionStarted,
)
from src.shared.infrastructure.event_bus_interface import IEventBus
from src.shared.infrastructure.notify_service import NotifyService

logger = logging.getLogger(__name__)


def register_activity_event_handlers(bus: IEventBus, notify_service: NotifyService) -> None:

    @bus.subscribe(WorkoutSessionStarted)
    async def on_session_started(event: WorkoutSessionStarted) -> None:
        logger.info(
            "Activity | SessionStarted session_id=%d user_id=%d plan_training_id=%s started_at=%s",
            event.session_id,
            event.user_id,
            event.plan_training_id,
            event.started_at.isoformat(),
        )
        notify_service.notify(event)

    @bus.subscribe(WorkoutSessionEnded)
    async def on_session_ended(event: WorkoutSessionEnded) -> None:
        logger.info(
            "Activity | SessionEnded session_id=%d user_id=%d duration_minutes=%s ended_at=%s",
            event.session_id,
            event.user_id,
            event.duration_minutes,
            event.ended_at.isoformat(),
        )
        notify_service.notify(event)

    @bus.subscribe(PersonalRecordBeaten)
    async def on_personal_record_beaten(event: PersonalRecordBeaten) -> None:
        logger.info(
            "Activity | PersonalRecordBeaten user_id=%d exercise_id=%d new_weight_kg=%.2f previous_weight_kg=%s",
            event.user_id,
            event.exercise_id,
            event.new_weight_kg,
            event.previous_weight_kg,
        )
        notify_service.notify(event)

    @bus.subscribe(WorkoutPlanCreated)
    async def on_plan_created(event: WorkoutPlanCreated) -> None:
        logger.info(
            "Activity | PlanCreated plan_id=%d author_id=%d title=%r is_public=%s",
            event.plan_id,
            event.author_id,
            event.title,
            event.is_public,
        )
        notify_service.notify(event)

    @bus.subscribe(WorkoutPlanMadePublic)
    async def on_plan_made_public(event: WorkoutPlanMadePublic) -> None:
        logger.info(
            "Activity | PlanMadePublic plan_id=%d author_id=%d title=%r",
            event.plan_id,
            event.author_id,
            event.title,
        )
        notify_service.notify(event)

    @bus.subscribe(WorkoutPlanDeleted)
    async def on_plan_deleted(event: WorkoutPlanDeleted) -> None:
        logger.info(
            "Activity | PlanDeleted plan_id=%d author_id=%d",
            event.plan_id,
            event.author_id,
        )
        notify_service.notify(event)
