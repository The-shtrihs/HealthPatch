import logging

from src.core_context.activity.contracts import events as integration
from src.core_context.activity.domain.events import (
    PersonalRecordBeaten as DomainPersonalRecordBeaten,
)
from src.core_context.activity.domain.events import (
    WorkoutCompletedEvent,
    WorkoutPlanCreated,
    WorkoutPlanPublished,
)
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


def register_activity_integration_publishers(bus: IEventBus) -> None:
    @bus.subscribe(WorkoutCompletedEvent, mode="sync")
    async def _on_workout_completed(event: WorkoutCompletedEvent) -> None:
        await bus.publish(
            integration.WorkoutCompleted(
                user_id=event.user_id,
                duration_minutes=event.duration_minutes,
                total_volume_kg=event.volume_kg,
            )
        )

    @bus.subscribe(DomainPersonalRecordBeaten, mode="sync")
    async def _on_pr_beaten(event: DomainPersonalRecordBeaten) -> None:
        await bus.publish(
            integration.PersonalRecordBeaten(
                user_id=event.user_id,
                exercise_id=event.exercise_id,
                new_weight_kg=event.new_weight_kg,
                previous_weight_kg=event.previous_weight_kg,
            )
        )

    @bus.subscribe(WorkoutPlanCreated, mode="sync")
    async def _on_plan_created(event: WorkoutPlanCreated) -> None:
        await bus.publish(
            integration.WorkoutPlanCreated(
                plan_id=event.plan_id,
                author_user_id=event.author_id,
                title=event.title,
                is_public=event.is_public,
            )
        )

    @bus.subscribe(WorkoutPlanPublished, mode="sync")
    async def _on_plan_published(event: WorkoutPlanPublished) -> None:
        await bus.publish(
            integration.WorkoutPlanPublished(
                plan_id=event.plan_id,
                author_user_id=event.author_id,
                title=event.title,
            )
        )
