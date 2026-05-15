import logging
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.analytics_context.audit.acl import translators as acl
from src.analytics_context.audit.domain.models import AuditEntry
from src.analytics_context.audit.infrastructure.repository import AuditEntryRepository
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
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


_session_factory: async_sessionmaker[AsyncSession] | None = None


def configure(session_factory: async_sessionmaker[AsyncSession]) -> None:
    global _session_factory
    _session_factory = session_factory


async def _persist(entry: AuditEntry) -> None:
    if _session_factory is None:
        logger.warning("Audit handler invoked but session factory not configured; dropping %s", entry.event_type)
        return
    async with _session_factory() as session:
        async with session.begin():
            repo = AuditEntryRepository(session)
            await repo.add(entry)


async def audit_user_registered(payload: dict[str, Any]) -> None:
    await _persist(acl.from_user_registered(UserRegistered(**payload)))


async def audit_user_logged_in(payload: dict[str, Any]) -> None:
    await _persist(acl.from_user_logged_in(UserLoggedIn(**payload)))


async def audit_password_reset_requested(payload: dict[str, Any]) -> None:
    await _persist(acl.from_password_reset_requested(PasswordResetRequested(**payload)))


async def audit_workout_completed(payload: dict[str, Any]) -> None:
    await _persist(acl.from_workout_completed(WorkoutCompleted(**payload)))


async def audit_personal_record_beaten(payload: dict[str, Any]) -> None:
    await _persist(acl.from_personal_record_beaten(PersonalRecordBeaten(**payload)))


async def audit_workout_plan_created(payload: dict[str, Any]) -> None:
    await _persist(acl.from_workout_plan_created(WorkoutPlanCreated(**payload)))


async def audit_workout_plan_published(payload: dict[str, Any]) -> None:
    await _persist(acl.from_workout_plan_published(WorkoutPlanPublished(**payload)))


async def audit_meal_entry_added(payload: dict[str, Any]) -> None:
    await _persist(acl.from_meal_entry_added(MealEntryAdded(**payload)))


async def audit_meal_entry_updated(payload: dict[str, Any]) -> None:
    await _persist(acl.from_meal_entry_updated(MealEntryUpdated(**payload)))


async def audit_meal_entry_deleted(payload: dict[str, Any]) -> None:
    await _persist(acl.from_meal_entry_deleted(MealEntryDeleted(**payload)))


async def audit_daily_norm_achieved(payload: dict[str, Any]) -> None:
    await _persist(acl.from_daily_norm_achieved(DailyNormAchieved(**payload)))


ASYNC_AUDIT_HANDLERS: list[tuple[type, str, Callable[[dict[str, Any]], Awaitable[None]]]] = [
    (UserRegistered, "audit_user_registered", audit_user_registered),
    (UserLoggedIn, "audit_user_logged_in", audit_user_logged_in),
    (PasswordResetRequested, "audit_password_reset_requested", audit_password_reset_requested),
    (WorkoutCompleted, "audit_workout_completed", audit_workout_completed),
    (PersonalRecordBeaten, "audit_personal_record_beaten", audit_personal_record_beaten),
    (WorkoutPlanCreated, "audit_workout_plan_created", audit_workout_plan_created),
    (WorkoutPlanPublished, "audit_workout_plan_published", audit_workout_plan_published),
    (MealEntryAdded, "audit_meal_entry_added", audit_meal_entry_added),
    (MealEntryUpdated, "audit_meal_entry_updated", audit_meal_entry_updated),
    (MealEntryDeleted, "audit_meal_entry_deleted", audit_meal_entry_deleted),
    (DailyNormAchieved, "audit_daily_norm_achieved", audit_daily_norm_achieved),
]


def register_audit_handlers(bus: IEventBus) -> None:
    for event_type, task_name, handler_fn in ASYNC_AUDIT_HANDLERS:
        bus.subscribe(event_type, mode="async", task_name=task_name)(handler_fn)
