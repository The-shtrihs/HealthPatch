from dataclasses import dataclass

from src.core_context.activity.contracts import events as activity_events
from src.core_context.nutrition.contracts import events as nutrition_events


@dataclass(frozen=True)
class XpAwardCommand:
    user_id: int
    reason: str
    source_event_id: str | None = None
    duration_minutes: int | None = None
    volume_kg: float | None = None


def from_workout_completed(event: activity_events.WorkoutCompleted) -> XpAwardCommand:
    return XpAwardCommand(
        user_id=event.user_id,
        reason="workout_completed",
        source_event_id=str(event.event_id),
        duration_minutes=int(event.duration_minutes or 0),
        volume_kg=event.total_volume_kg,
    )


def from_meal_entry_added(event: nutrition_events.MealEntryAdded) -> XpAwardCommand:
    return XpAwardCommand(
        user_id=event.user_id,
        reason="meal_entry_added",
        source_event_id=str(event.event_id),
    )


def from_meal_entry_updated(event: nutrition_events.MealEntryUpdated) -> XpAwardCommand:
    return XpAwardCommand(
        user_id=event.user_id,
        reason="meal_entry_updated",
        source_event_id=str(event.event_id),
    )


def from_daily_norm_achieved(event: nutrition_events.DailyNormAchieved) -> XpAwardCommand:
    return XpAwardCommand(
        user_id=event.user_id,
        reason="daily_norm_achieved",
        source_event_id=str(event.event_id),
    )
