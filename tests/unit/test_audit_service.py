from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.activity.application.audit_service import IActivityAuditService
from src.activity.application.event_handlers import register_activity_event_handlers
from src.activity.domain.events import WorkoutPlanCreated, WorkoutSessionStarted
from src.shared.infrastructure.in_memory_event_bus import InMemoryEventBus


class RecordingAuditService(IActivityAuditService):
    def __init__(self) -> None:
        self.records: list = []

    async def record(self, event) -> None:
        self.records.append(event)


class FailingAuditService(IActivityAuditService):
    async def record(self, event) -> None:
        raise RuntimeError("audit sink unavailable")


@pytest.mark.asyncio
class TestAsyncAuditPath:
    async def test_audit_receives_event_via_bus(self) -> None:
        bus = InMemoryEventBus()
        audit = RecordingAuditService()
        register_activity_event_handlers(bus, audit)

        event = WorkoutPlanCreated(plan_id=11, author_id=7, title="PPL", is_public=False)
        await bus.publish(event)

        assert audit.records == [event]

    async def test_audit_failure_does_not_break_other_subscribers(self) -> None:
        bus = InMemoryEventBus()
        register_activity_event_handlers(bus, FailingAuditService())

        called = []

        @bus.subscribe(WorkoutPlanCreated)
        async def other(evt: WorkoutPlanCreated) -> None:
            called.append(evt)

        event = WorkoutPlanCreated(plan_id=1, author_id=1, title="x", is_public=True)
        try:
            await bus.publish(event)
        except RuntimeError:
            pytest.fail("publish() must isolate subscriber failures")

        assert called == [event]


@pytest.mark.asyncio
class TestSyncAuditPath:
    async def test_start_session_sync_audit_called_after_persist(self) -> None:
        from src.activity.application.commands import StartSessionCommand
        from src.activity.application.handlers.start_session import StartSessionCommandHandler
        from tests.unit.test_activity import FakeActivityRepository, FakeUnitOfWork

        repo = FakeActivityRepository()
        uow = FakeUnitOfWork(repo)
        bus = AsyncMock()
        audit = RecordingAuditService()

        handler = StartSessionCommandHandler(uow, bus, audit)
        session_id = await handler.handle(StartSessionCommand(user_id=42, plan_training_id=None))

        assert session_id is not None
        assert len(audit.records) == 1
        rec = audit.records[0]
        assert isinstance(rec, WorkoutSessionStarted)
        assert rec.session_id == session_id
        assert rec.user_id == 42

    async def test_start_session_swallows_audit_failures(self) -> None:
        from src.activity.application.commands import StartSessionCommand
        from src.activity.application.handlers.start_session import StartSessionCommandHandler
        from tests.unit.test_activity import FakeActivityRepository, FakeUnitOfWork

        repo = FakeActivityRepository()
        uow = FakeUnitOfWork(repo)
        bus = AsyncMock()

        handler = StartSessionCommandHandler(uow, bus, FailingAuditService())
        session_id = await handler.handle(
            StartSessionCommand(user_id=1, plan_training_id=None),
        )
        assert isinstance(session_id, int)
