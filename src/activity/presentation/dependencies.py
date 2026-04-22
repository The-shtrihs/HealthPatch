from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.activity.application.use_cases.exercise_catalog import (
    CreateExerciseUseCase,
    CreateMuscleGroupUseCase,
    GetExerciseUseCase,
    ListExercisesUseCase,
    ListMuscleGroupsUseCase,
)
from src.activity.application.use_cases.personal_record import (
    DeletePersonalRecordUseCase,
    ListPersonalRecordsUseCase,
    UpsertPersonalRecordUseCase,
)
from src.activity.application.use_cases.workout_plan import (
    AddExerciseToTrainingUseCase,
    AddTrainingUseCase,
    CreatePlanUseCase,
    DeletePlanUseCase,
    DeleteTrainingExerciseUseCase,
    DeleteTrainingUseCase,
    GetPlanUseCase,
    ListPublicPlansUseCase,
    ListUserPlansUseCase,
    UpdatePlanUseCase,
)
from src.activity.application.use_cases.workout_session import (
    AddExerciseToSessionUseCase,
    EndSessionUseCase,
    GetSessionDetailUseCase,
    ListUserSessionsUseCase,
    LogSetUseCase,
    StartSessionUseCase,
)
from src.activity.infrastructure.unit_of_work import SqlAlchemyActivityUnitOfWork
from src.core.database import get_session


async def get_activity_uow(db: AsyncSession = Depends(get_session)) -> SqlAlchemyActivityUnitOfWork:
    return SqlAlchemyActivityUnitOfWork(db)


# ---- Exercise catalog ----


async def get_list_muscle_groups_uc(uow=Depends(get_activity_uow)) -> ListMuscleGroupsUseCase:
    return ListMuscleGroupsUseCase(uow)


async def get_create_muscle_group_uc(uow=Depends(get_activity_uow)) -> CreateMuscleGroupUseCase:
    return CreateMuscleGroupUseCase(uow)


async def get_list_exercises_uc(uow=Depends(get_activity_uow)) -> ListExercisesUseCase:
    return ListExercisesUseCase(uow)


async def get_get_exercise_uc(uow=Depends(get_activity_uow)) -> GetExerciseUseCase:
    return GetExerciseUseCase(uow)


async def get_create_exercise_uc(uow=Depends(get_activity_uow)) -> CreateExerciseUseCase:
    return CreateExerciseUseCase(uow)


# ---- Workout plans ----


async def get_list_public_plans_uc(uow=Depends(get_activity_uow)) -> ListPublicPlansUseCase:
    return ListPublicPlansUseCase(uow)


async def get_list_user_plans_uc(uow=Depends(get_activity_uow)) -> ListUserPlansUseCase:
    return ListUserPlansUseCase(uow)


async def get_get_plan_uc(uow=Depends(get_activity_uow)) -> GetPlanUseCase:
    return GetPlanUseCase(uow)


async def get_create_plan_uc(uow=Depends(get_activity_uow)) -> CreatePlanUseCase:
    return CreatePlanUseCase(uow)


async def get_update_plan_uc(uow=Depends(get_activity_uow)) -> UpdatePlanUseCase:
    return UpdatePlanUseCase(uow)


async def get_delete_plan_uc(uow=Depends(get_activity_uow)) -> DeletePlanUseCase:
    return DeletePlanUseCase(uow)


async def get_add_training_uc(uow=Depends(get_activity_uow)) -> AddTrainingUseCase:
    return AddTrainingUseCase(uow)


async def get_delete_training_uc(uow=Depends(get_activity_uow)) -> DeleteTrainingUseCase:
    return DeleteTrainingUseCase(uow)


async def get_add_exercise_to_training_uc(
    uow=Depends(get_activity_uow),
) -> AddExerciseToTrainingUseCase:
    return AddExerciseToTrainingUseCase(uow)


async def get_delete_training_exercise_uc(
    uow=Depends(get_activity_uow),
) -> DeleteTrainingExerciseUseCase:
    return DeleteTrainingExerciseUseCase(uow)


# ---- Workout sessions ----


async def get_start_session_uc(uow=Depends(get_activity_uow)) -> StartSessionUseCase:
    return StartSessionUseCase(uow)


async def get_end_session_uc(uow=Depends(get_activity_uow)) -> EndSessionUseCase:
    return EndSessionUseCase(uow)


async def get_session_detail_uc(uow=Depends(get_activity_uow)) -> GetSessionDetailUseCase:
    return GetSessionDetailUseCase(uow)


async def get_list_user_sessions_uc(uow=Depends(get_activity_uow)) -> ListUserSessionsUseCase:
    return ListUserSessionsUseCase(uow)


async def get_add_exercise_to_session_uc(
    uow=Depends(get_activity_uow),
) -> AddExerciseToSessionUseCase:
    return AddExerciseToSessionUseCase(uow)


async def get_log_set_uc(uow=Depends(get_activity_uow)) -> LogSetUseCase:
    return LogSetUseCase(uow)


# ---- Personal records ----


async def get_list_personal_records_uc(
    uow=Depends(get_activity_uow),
) -> ListPersonalRecordsUseCase:
    return ListPersonalRecordsUseCase(uow)


async def get_upsert_personal_record_uc(
    uow=Depends(get_activity_uow),
) -> UpsertPersonalRecordUseCase:
    return UpsertPersonalRecordUseCase(uow)


async def get_delete_personal_record_uc(
    uow=Depends(get_activity_uow),
) -> DeletePersonalRecordUseCase:
    return DeletePersonalRecordUseCase(uow)
