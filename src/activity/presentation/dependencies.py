from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.activity.application.handlers.add_exercise_to_session import AddExerciseToSessionCommandHandler
from src.activity.application.handlers.add_exercise_to_training import AddExerciseToTrainingCommandHandler
from src.activity.application.handlers.add_training import AddTrainingCommandHandler
from src.activity.application.handlers.create_exercise import CreateExerciseCommandHandler
from src.activity.application.handlers.create_muscle_group import CreateMuscleGroupCommandHandler
from src.activity.application.handlers.create_workout_plan import CreateWorkoutPlanCommandHandler
from src.activity.application.handlers.delete_personal_record import DeletePersonalRecordCommandHandler
from src.activity.application.handlers.delete_training import DeleteTrainingCommandHandler
from src.activity.application.handlers.delete_training_exercise import DeleteTrainingExerciseCommandHandler
from src.activity.application.handlers.delete_workout_plan import DeleteWorkoutPlanCommandHandler
from src.activity.application.handlers.end_session import EndSessionCommandHandler
from src.activity.application.handlers.get_exercise import GetExerciseQueryHandler
from src.activity.application.handlers.get_plan_detail import GetPlanDetailQueryHandler
from src.activity.application.handlers.get_session_detail import GetSessionDetailQueryHandler
from src.activity.application.handlers.list_exercises import ListExercisesQueryHandler
from src.activity.application.handlers.list_muscle_groups import ListMuscleGroupsQueryHandler
from src.activity.application.handlers.list_my_plans import ListMyPlansQueryHandler
from src.activity.application.handlers.list_personal_records import ListPersonalRecordsQueryHandler
from src.activity.application.handlers.list_public_plans import ListPublicPlansQueryHandler
from src.activity.application.handlers.list_user_sessions import ListUserSessionsQueryHandler
from src.activity.application.handlers.log_set import LogSetCommandHandler
from src.activity.application.handlers.start_session import StartSessionCommandHandler
from src.activity.application.handlers.update_workout_plan import UpdateWorkoutPlanCommandHandler
from src.activity.application.handlers.upsert_personal_record import UpsertPersonalRecordCommandHandler
from src.activity.infrastructure.read_repository import SqlAlchemyActivityReadRepository
from src.activity.infrastructure.unit_of_work import SqlAlchemyActivityUnitOfWork
from src.core.database import get_session


async def get_activity_uow(db: AsyncSession = Depends(get_session)) -> SqlAlchemyActivityUnitOfWork:
    return SqlAlchemyActivityUnitOfWork(db)


async def get_activity_read_repo(db: AsyncSession = Depends(get_session)) -> SqlAlchemyActivityReadRepository:
    return SqlAlchemyActivityReadRepository(db)


# ---- Command handlers ----


async def get_create_muscle_group_handler(uow=Depends(get_activity_uow)) -> CreateMuscleGroupCommandHandler:
    return CreateMuscleGroupCommandHandler(uow)


async def get_create_exercise_handler(uow=Depends(get_activity_uow)) -> CreateExerciseCommandHandler:
    return CreateExerciseCommandHandler(uow)


async def get_create_workout_plan_handler(uow=Depends(get_activity_uow)) -> CreateWorkoutPlanCommandHandler:
    return CreateWorkoutPlanCommandHandler(uow)


async def get_update_workout_plan_handler(uow=Depends(get_activity_uow)) -> UpdateWorkoutPlanCommandHandler:
    return UpdateWorkoutPlanCommandHandler(uow)


async def get_delete_workout_plan_handler(uow=Depends(get_activity_uow)) -> DeleteWorkoutPlanCommandHandler:
    return DeleteWorkoutPlanCommandHandler(uow)


async def get_add_training_handler(uow=Depends(get_activity_uow)) -> AddTrainingCommandHandler:
    return AddTrainingCommandHandler(uow)


async def get_delete_training_handler(uow=Depends(get_activity_uow)) -> DeleteTrainingCommandHandler:
    return DeleteTrainingCommandHandler(uow)


async def get_add_exercise_to_training_handler(uow=Depends(get_activity_uow)) -> AddExerciseToTrainingCommandHandler:
    return AddExerciseToTrainingCommandHandler(uow)


async def get_delete_training_exercise_handler(uow=Depends(get_activity_uow)) -> DeleteTrainingExerciseCommandHandler:
    return DeleteTrainingExerciseCommandHandler(uow)


async def get_start_session_handler(uow=Depends(get_activity_uow)) -> StartSessionCommandHandler:
    return StartSessionCommandHandler(uow)


async def get_end_session_handler(uow=Depends(get_activity_uow)) -> EndSessionCommandHandler:
    return EndSessionCommandHandler(uow)


async def get_add_exercise_to_session_handler(uow=Depends(get_activity_uow)) -> AddExerciseToSessionCommandHandler:
    return AddExerciseToSessionCommandHandler(uow)


async def get_log_set_handler(uow=Depends(get_activity_uow)) -> LogSetCommandHandler:
    return LogSetCommandHandler(uow)


async def get_upsert_personal_record_handler(uow=Depends(get_activity_uow)) -> UpsertPersonalRecordCommandHandler:
    return UpsertPersonalRecordCommandHandler(uow)


async def get_delete_personal_record_handler(uow=Depends(get_activity_uow)) -> DeletePersonalRecordCommandHandler:
    return DeletePersonalRecordCommandHandler(uow)


# ---- Query handlers ----


async def get_list_muscle_groups_handler(read_repo=Depends(get_activity_read_repo)) -> ListMuscleGroupsQueryHandler:
    return ListMuscleGroupsQueryHandler(read_repo)


async def get_list_exercises_handler(read_repo=Depends(get_activity_read_repo)) -> ListExercisesQueryHandler:
    return ListExercisesQueryHandler(read_repo)


async def get_get_exercise_handler(read_repo=Depends(get_activity_read_repo)) -> GetExerciseQueryHandler:
    return GetExerciseQueryHandler(read_repo)


async def get_list_public_plans_handler(read_repo=Depends(get_activity_read_repo)) -> ListPublicPlansQueryHandler:
    return ListPublicPlansQueryHandler(read_repo)


async def get_list_my_plans_handler(read_repo=Depends(get_activity_read_repo)) -> ListMyPlansQueryHandler:
    return ListMyPlansQueryHandler(read_repo)


async def get_get_plan_detail_handler(read_repo=Depends(get_activity_read_repo)) -> GetPlanDetailQueryHandler:
    return GetPlanDetailQueryHandler(read_repo)


async def get_list_user_sessions_handler(read_repo=Depends(get_activity_read_repo)) -> ListUserSessionsQueryHandler:
    return ListUserSessionsQueryHandler(read_repo)


async def get_get_session_detail_handler(read_repo=Depends(get_activity_read_repo)) -> GetSessionDetailQueryHandler:
    return GetSessionDetailQueryHandler(read_repo)


async def get_list_personal_records_handler(read_repo=Depends(get_activity_read_repo)) -> ListPersonalRecordsQueryHandler:
    return ListPersonalRecordsQueryHandler(read_repo)
