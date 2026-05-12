import logging

from src.activity.domain.events import (
    WorkoutCompletedEvent,
    WorkoutSessionStarted,
    WorkoutSessionEnded,
    ExerciseSessionAdded,
    SetLogged,
    PersonalRecordBeaten,
    PersonalRecordUpserted,
    WorkoutPlanCreated,
    WorkoutPlanMadePublic,
    WorkoutPlanDeleted,
)
from src.auth.domain.events import UserRegisteredEvent, PasswordResetRequestedEvent, VerificationEmailRequestedEvent
from src.shared.infrastructure.notify_service import NotifyService
from src.nutrition.domain.events import (
    MealEntryAddedEvent,
    MealEntryUpdatedEvent,
    MealEntryDeletedEvent,
    DailyDiaryUpdatedEvent,
    DailyNormAchievedEvent,
)
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


def register_event_notification_handlers(bus: IEventBus, notify_service: NotifyService) -> None:
    """
    Register all event handlers for event notifications.
    
    Subscribes to all domain events from nutrition, activity, and auth domains,
    routing them to the notify service for logging/delivery.
    
    Args:
        bus: Event bus to subscribe to
        notify_service: Notification service implementation (logging, push, email, etc.)
    """

    # Nutrition events
    @bus.subscribe(MealEntryAddedEvent)
    async def on_meal_entry_added(event: MealEntryAddedEvent) -> None:
        await notify_service.notify(event)

    @bus.subscribe(MealEntryUpdatedEvent)
    async def on_meal_entry_updated(event: MealEntryUpdatedEvent) -> None:
        await notify_service.notify(event)

    @bus.subscribe(MealEntryDeletedEvent)
    async def on_meal_entry_deleted(event: MealEntryDeletedEvent) -> None:
        await notify_service.notify(event)

    @bus.subscribe(DailyDiaryUpdatedEvent)
    async def on_daily_diary_updated(event: DailyDiaryUpdatedEvent) -> None:
        await notify_service.notify(event)

    @bus.subscribe(DailyNormAchievedEvent)
    async def on_daily_norm_achieved(event: DailyNormAchievedEvent) -> None:
        await notify_service.notify(event)

    # Activity events
    @bus.subscribe(WorkoutSessionStarted)
    async def on_workout_session_started(event: WorkoutSessionStarted) -> None:
        await notify_service.notify(event)

    @bus.subscribe(WorkoutSessionEnded)
    async def on_workout_session_ended(event: WorkoutSessionEnded) -> None:
        await notify_service.notify(event)

    @bus.subscribe(ExerciseSessionAdded)
    async def on_exercise_session_added(event: ExerciseSessionAdded) -> None:
        await notify_service.notify(event)

    @bus.subscribe(SetLogged)
    async def on_set_logged(event: SetLogged) -> None:
        await notify_service.notify(event)

    @bus.subscribe(PersonalRecordBeaten)
    async def on_personal_record_beaten(event: PersonalRecordBeaten) -> None:
        await notify_service.notify(event)

    @bus.subscribe(PersonalRecordUpserted)
    async def on_personal_record_upserted(event: PersonalRecordUpserted) -> None:
        await notify_service.notify(event)

    @bus.subscribe(WorkoutPlanCreated)
    async def on_workout_plan_created(event: WorkoutPlanCreated) -> None:
        await notify_service.notify(event)

    @bus.subscribe(WorkoutPlanMadePublic)
    async def on_workout_plan_made_public(event: WorkoutPlanMadePublic) -> None:
        await notify_service.notify(event)

    @bus.subscribe(WorkoutPlanDeleted)
    async def on_workout_plan_deleted(event: WorkoutPlanDeleted) -> None:
        await notify_service.notify(event)

    @bus.subscribe(WorkoutCompletedEvent)
    async def on_workout_completed(event: WorkoutCompletedEvent) -> None:
        await notify_service.notify(event)

    # Auth events
    @bus.subscribe(UserRegisteredEvent)
    async def on_user_registered(event: UserRegisteredEvent) -> None:
        await notify_service.notify(event)

    @bus.subscribe(PasswordResetRequestedEvent)
    async def on_password_reset_requested(event: PasswordResetRequestedEvent) -> None:
        await notify_service.notify(event)

    @bus.subscribe(VerificationEmailRequestedEvent)
    async def on_verification_email_requested(event: VerificationEmailRequestedEvent) -> None:
        await notify_service.notify(event)
