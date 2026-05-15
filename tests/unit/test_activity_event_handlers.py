from datetime import UTC, datetime

import pytest

from src.core_context.activity.application.event_handlers import register_activity_event_handlers
from src.core_context.activity.domain.events import (
    PersonalRecordBeaten,
    WorkoutPlanCreated,
    WorkoutPlanDeleted,
    WorkoutPlanPublished,
    WorkoutSessionEnded,
    WorkoutSessionStarted,
)
from src.core_context.activity.infrastructure.audit_service import LoggingActivityAuditService
from src.shared.infrastructure.in_memory_event_bus import InMemoryEventBus


@pytest.fixture
def bus() -> InMemoryEventBus:
    b = InMemoryEventBus()
    register_activity_event_handlers(b, LoggingActivityAuditService())
    return b


@pytest.mark.asyncio
class TestActivityEventHandlers:
    async def test_session_started_is_logged(self, bus, caplog):
        event = WorkoutSessionStarted(
            session_id=1,
            user_id=42,
            plan_training_id=None,
            started_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
        )
        with caplog.at_level("INFO"):
            await bus.publish(event)
        assert "SessionStarted" in caplog.text
        assert "session_id=1" in caplog.text
        assert "user_id=42" in caplog.text

    async def test_session_ended_is_logged(self, bus, caplog):
        event = WorkoutSessionEnded(
            session_id=2,
            user_id=42,
            ended_at=datetime(2026, 1, 1, 11, 0, 0, tzinfo=UTC),
            duration_minutes=60.0,
        )
        with caplog.at_level("INFO"):
            await bus.publish(event)
        assert "SessionEnded" in caplog.text
        assert "session_id=2" in caplog.text
        assert "duration_minutes=60.0" in caplog.text

    async def test_personal_record_beaten_first_record_logged(self, bus, caplog):
        event = PersonalRecordBeaten(
            user_id=42,
            exercise_id=7,
            new_weight_kg=100.0,
            previous_weight_kg=None,
            recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        with caplog.at_level("INFO"):
            await bus.publish(event)
        assert "PersonalRecordBeaten" in caplog.text
        assert "user_id=42" in caplog.text
        assert "100.00" in caplog.text

    async def test_personal_record_beaten_improvement_logged(self, bus, caplog):
        event = PersonalRecordBeaten(
            user_id=42,
            exercise_id=7,
            new_weight_kg=120.0,
            previous_weight_kg=100.0,
            recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        with caplog.at_level("INFO"):
            await bus.publish(event)
        assert "120.00" in caplog.text
        assert "100.0" in caplog.text

    async def test_plan_created_is_logged(self, bus, caplog):
        event = WorkoutPlanCreated(plan_id=5, author_id=42, title="Push/Pull/Legs", is_public=True)
        with caplog.at_level("INFO"):
            await bus.publish(event)
        assert "PlanCreated" in caplog.text
        assert "plan_id=5" in caplog.text
        assert "Push/Pull/Legs" in caplog.text

    async def test_plan_published_is_logged(self, bus, caplog):
        event = WorkoutPlanPublished(plan_id=5, author_id=42, title="Push/Pull/Legs")
        with caplog.at_level("INFO"):
            await bus.publish(event)
        assert "PlanPublished" in caplog.text
        assert "plan_id=5" in caplog.text

    async def test_plan_deleted_is_logged(self, bus, caplog):
        event = WorkoutPlanDeleted(plan_id=5, author_id=42)
        with caplog.at_level("INFO"):
            await bus.publish(event)
        assert "PlanDeleted" in caplog.text
        assert "plan_id=5" in caplog.text

    async def test_unrelated_event_does_not_raise(self, bus: InMemoryEventBus):
        from src.core_context.activity.domain.events import SetLogged

        event = SetLogged(
            set_id=1,
            session_id=1,
            exercise_session_id=1,
            exercise_id=1,
            user_id=1,
            set_number=1,
            reps=5,
            weight_kg=60.0,
        )
        await bus.publish(event)


@pytest.mark.asyncio
class TestLogSetDispatchesEvents:
    async def test_log_set_publishes_set_logged(self):

        from src.core_context.activity.application.commands import LogSetCommand
        from src.core_context.activity.application.handlers.log_set import LogSetCommandHandler
        from src.core_context.activity.domain.events import SetLogged
        from tests.unit.test_activity import FakeActivityRepository, FakeUnitOfWork

        repo = FakeActivityRepository()
        mg = await repo.create_muscle_group("chest")
        ex = await repo.create_exercise("bench", mg.id, [])
        session = await repo.create_session(user_id=1, plan_training_id=None, started_at=datetime.now(UTC))
        es = await repo.add_exercise_to_session(workout_session_id=session.id, exercise_id=ex.id, order_num=1, is_from_template=False)

        received: list[SetLogged] = []
        bus = InMemoryEventBus()

        @bus.subscribe(SetLogged)
        async def capture(event: SetLogged) -> None:
            received.append(event)

        uow = FakeUnitOfWork(repo)
        handler = LogSetCommandHandler(uow, bus)
        await handler.handle(LogSetCommand(session_id=session.id, exercise_session_id=es.id, user_id=1, set_number=1, reps=5, weight=80.0))

        assert len(received) == 1
        assert received[0].user_id == 1
        assert received[0].weight_kg == 80.0

    async def test_log_set_publishes_personal_record_beaten_on_new_pr(self):
        from src.core_context.activity.application.commands import LogSetCommand
        from src.core_context.activity.application.handlers.log_set import LogSetCommandHandler
        from src.core_context.activity.domain.events import PersonalRecordBeaten
        from tests.unit.test_activity import FakeActivityRepository, FakeUnitOfWork

        repo = FakeActivityRepository()
        mg = await repo.create_muscle_group("legs")
        ex = await repo.create_exercise("squat", mg.id, [])
        session = await repo.create_session(user_id=1, plan_training_id=None, started_at=datetime.now(UTC))
        es = await repo.add_exercise_to_session(workout_session_id=session.id, exercise_id=ex.id, order_num=1, is_from_template=False)

        pr_events: list[PersonalRecordBeaten] = []
        bus = InMemoryEventBus()

        @bus.subscribe(PersonalRecordBeaten)
        async def capture(event: PersonalRecordBeaten) -> None:
            pr_events.append(event)

        uow = FakeUnitOfWork(repo)
        await LogSetCommandHandler(uow, bus).handle(
            LogSetCommand(session_id=session.id, exercise_session_id=es.id, user_id=1, set_number=1, reps=5, weight=100.0)
        )

        assert len(pr_events) == 1
        assert pr_events[0].new_weight_kg == 100.0
        assert pr_events[0].previous_weight_kg is None

    async def test_log_set_no_pr_event_when_weight_not_higher(self):
        from datetime import UTC, datetime

        from src.core_context.activity.application.commands import LogSetCommand
        from src.core_context.activity.application.handlers.log_set import LogSetCommandHandler
        from src.core_context.activity.domain.events import PersonalRecordBeaten
        from tests.unit.test_activity import FakeActivityRepository, FakeUnitOfWork

        repo = FakeActivityRepository()
        mg = await repo.create_muscle_group("back")
        ex = await repo.create_exercise("row", mg.id, [])
        await repo.upsert_personal_record(user_id=1, exercise_id=ex.id, weight=120.0, recorded_at=datetime.now(UTC))
        session = await repo.create_session(user_id=1, plan_training_id=None, started_at=datetime.now(UTC))
        es = await repo.add_exercise_to_session(workout_session_id=session.id, exercise_id=ex.id, order_num=1, is_from_template=False)

        pr_events: list[PersonalRecordBeaten] = []
        bus = InMemoryEventBus()

        @bus.subscribe(PersonalRecordBeaten)
        async def capture(event: PersonalRecordBeaten) -> None:
            pr_events.append(event)

        uow = FakeUnitOfWork(repo)
        await LogSetCommandHandler(uow, bus).handle(
            LogSetCommand(session_id=session.id, exercise_session_id=es.id, user_id=1, set_number=1, reps=5, weight=100.0)
        )

        assert pr_events == []
