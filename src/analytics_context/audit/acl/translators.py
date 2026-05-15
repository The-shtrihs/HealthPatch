from src.analytics_context.audit.domain.models import AuditChannel, AuditEntry
from src.core_context.activity.contracts.events import (
    PersonalRecordBeaten,
    WorkoutCompleted,
    WorkoutPlanCreated,
    WorkoutPlanPublished,
)
from src.core_context.auth.contracts.events import (
    PasswordResetRequested,
    UserLoggedIn,
    UserRegistered,
)
from src.core_context.nutrition.contracts.events import (
    DailyNormAchieved,
    MealEntryAdded,
    MealEntryDeleted,
    MealEntryUpdated,
)
from src.shared.contracts.integration_event import IntegrationEvent


def _to_entry(event: IntegrationEvent, channel: AuditChannel, user_id: int | None) -> AuditEntry:
    payload = event.model_dump(mode="json")
    payload.pop("event_id", None)
    payload.pop("occurred_at", None)
    payload.pop("schema_version", None)
    return AuditEntry(
        channel=channel,
        event_type=type(event).__name__,
        user_id=user_id,
        occurred_at=event.occurred_at,
        payload=payload,
    )


def from_user_registered(event: UserRegistered) -> AuditEntry:
    return _to_entry(event, AuditChannel.AUTH, event.user_id)


def from_user_logged_in(event: UserLoggedIn) -> AuditEntry:
    return _to_entry(event, AuditChannel.AUTH, event.user_id)


def from_password_reset_requested(event: PasswordResetRequested) -> AuditEntry:
    return _to_entry(event, AuditChannel.AUTH, event.user_id)


def from_workout_completed(event: WorkoutCompleted) -> AuditEntry:
    return _to_entry(event, AuditChannel.ACTIVITY, event.user_id)


def from_personal_record_beaten(event: PersonalRecordBeaten) -> AuditEntry:
    return _to_entry(event, AuditChannel.ACTIVITY, event.user_id)


def from_workout_plan_created(event: WorkoutPlanCreated) -> AuditEntry:
    return _to_entry(event, AuditChannel.ACTIVITY, event.author_user_id)


def from_workout_plan_published(event: WorkoutPlanPublished) -> AuditEntry:
    return _to_entry(event, AuditChannel.ACTIVITY, event.author_user_id)


def from_meal_entry_added(event: MealEntryAdded) -> AuditEntry:
    return _to_entry(event, AuditChannel.NUTRITION, event.user_id)


def from_meal_entry_updated(event: MealEntryUpdated) -> AuditEntry:
    return _to_entry(event, AuditChannel.NUTRITION, event.user_id)


def from_meal_entry_deleted(event: MealEntryDeleted) -> AuditEntry:
    return _to_entry(event, AuditChannel.NUTRITION, event.user_id)


def from_daily_norm_achieved(event: DailyNormAchieved) -> AuditEntry:
    return _to_entry(event, AuditChannel.NUTRITION, event.user_id)
