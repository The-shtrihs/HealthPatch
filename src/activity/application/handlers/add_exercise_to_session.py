from src.activity.application.commands import AddExerciseToSessionCommand
from src.activity.domain.errors import NotResourceOwnerError, WorkoutSessionNotFoundError
from src.activity.domain.factory import ExerciseSessionFactory
from src.activity.domain.interfaces import IActivityUnitOfWork


class AddExerciseToSessionCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: AddExerciseToSessionCommand) -> int:
        async with self._uow:
            session = await self._uow.repo.get_session_by_id(cmd.session_id)
            if session is None:
                raise WorkoutSessionNotFoundError(cmd.session_id)
            if not session.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this session")
            session.ensure_can_be_modified("Cannot add exercises to an ended session")

            factory = ExerciseSessionFactory(self._uow.repo)
            await factory.create(
                workout_session_id=cmd.session_id,
                exercise_id=cmd.exercise_id,
                order_num=cmd.order_num,
                is_from_template=False,
            )

            es = await self._uow.repo.add_exercise_to_session(
                workout_session_id=cmd.session_id,
                exercise_id=cmd.exercise_id,
                order_num=cmd.order_num,
                is_from_template=False,
            )
        return es.id
