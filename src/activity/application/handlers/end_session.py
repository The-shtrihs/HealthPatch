from datetime import UTC, datetime

from src.activity.application.commands import EndSessionCommand
from src.activity.domain.errors import NotResourceOwnerError, WorkoutSessionNotFoundError
from src.activity.domain.events import WorkoutSessionEnded
from src.activity.domain.interfaces import IActivityUnitOfWork


class EndSessionCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: EndSessionCommand) -> None:
        async with self._uow:
            session = await self._uow.repo.get_session_by_id(cmd.session_id)
            if session is None:
                raise WorkoutSessionNotFoundError(cmd.session_id)
            if not session.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this session")
            session.end(datetime.now(UTC))
            await self._uow.repo.save_session(session)
            self._uow.events.append(
                WorkoutSessionEnded(
                    session_id=session.id,
                    user_id=session.user_id,
                    ended_at=session.ended_at,
                    duration_minutes=session.duration_minutes(),
                )
            )
