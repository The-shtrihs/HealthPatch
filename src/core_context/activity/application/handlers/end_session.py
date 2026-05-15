import logging
from datetime import UTC, datetime

from src.core_context.activity.application.commands import EndSessionCommand
from src.core_context.activity.domain.errors import NotResourceOwnerError, WorkoutSessionNotFoundError
from src.core_context.activity.domain.events import WorkoutCompletedEvent, WorkoutSessionEnded
from src.core_context.activity.domain.interfaces import IActivityUnitOfWork
from src.shared.application.dispatcher import dispatch_domain_events
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


class EndSessionCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork, bus: IEventBus) -> None:
        self._uow = uow
        self._bus = bus

    async def handle(self, cmd: EndSessionCommand) -> None:
        async with self._uow:
            session = await self._uow.repo.get_session_by_id(cmd.session_id)
            if session is None:
                raise WorkoutSessionNotFoundError(cmd.session_id)
            if not session.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this session")
            session.end(datetime.now(UTC))
            await self._uow.repo.save_session(session)
            duration = session.duration_minutes()
            volume = session.calculate_total_volume_kg()
            self._uow.events.append(
                WorkoutSessionEnded(
                    session_id=session.id,
                    user_id=session.user_id,
                    ended_at=session.ended_at,
                    duration_minutes=session.duration_minutes(),
                )
            )
            self._uow.events.append(
                WorkoutCompletedEvent(
                    user_id=session.user_id,
                    duration_minutes=duration,
                    volume_kg=volume,
                )
            )
        await dispatch_domain_events(self._uow, self._bus)
        logger.info("Session %d ended, events dispatched.", cmd.session_id)
