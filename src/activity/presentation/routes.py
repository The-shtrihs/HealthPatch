from fastapi import APIRouter, Depends, Query, status

from src.activity.application.commands import (
    AddExerciseToSessionCommand,
    AddExerciseToTrainingCommand,
    AddTrainingCommand,
    CreateExerciseCommand,
    CreateMuscleGroupCommand,
    CreateWorkoutPlanCommand,
    DeletePersonalRecordCommand,
    DeleteTrainingCommand,
    DeleteTrainingExerciseCommand,
    DeleteWorkoutPlanCommand,
    EndSessionCommand,
    LogSetCommand,
    PlanTrainingExerciseInput,
    PlanTrainingInput,
    StartSessionCommand,
    UpdateWorkoutPlanCommand,
    UpsertPersonalRecordCommand,
)
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
from src.activity.application.queries import (
    GetExerciseQuery,
    GetPlanDetailQuery,
    GetSessionDetailQuery,
    ListExercisesQuery,
    ListMuscleGroupsQuery,
    ListMyPlansQuery,
    ListPersonalRecordsQuery,
    ListPublicPlansQuery,
    ListUserSessionsQuery,
)
from src.activity.presentation.dependencies import (
    get_add_exercise_to_session_handler,
    get_add_exercise_to_training_handler,
    get_add_training_handler,
    get_create_exercise_handler,
    get_create_muscle_group_handler,
    get_create_workout_plan_handler,
    get_delete_personal_record_handler,
    get_delete_training_exercise_handler,
    get_delete_training_handler,
    get_delete_workout_plan_handler,
    get_end_session_handler,
    get_get_exercise_handler,
    get_get_plan_detail_handler,
    get_get_session_detail_handler,
    get_list_exercises_handler,
    get_list_muscle_groups_handler,
    get_list_my_plans_handler,
    get_list_personal_records_handler,
    get_list_public_plans_handler,
    get_list_user_sessions_handler,
    get_log_set_handler,
    get_start_session_handler,
    get_update_workout_plan_handler,
    get_upsert_personal_record_handler,
)
from src.activity.presentation.schemas import (
    AddExerciseToSessionRequest,
    AddExerciseToTrainingRequest,
    CreateExerciseRequest,
    CreateMuscleGroupRequest,
    CreatePlanTrainingRequest,
    CreateWorkoutPlanRequest,
    ExerciseListResponse,
    ExerciseResponse,
    IdResponse,
    LogSetRequest,
    MuscleGroupResponse,
    PersonalRecordResponse,
    PlanDetailResponse,
    SessionDetailResponse,
    SessionListResponse,
    StartSessionRequest,
    UpdateWorkoutPlanRequest,
    UpsertPersonalRecordRequest,
    WorkoutPlanListResponse,
)
from src.auth.presentation.dependencies import get_current_user
from src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE, MIN_PAGE_SIZE
from src.models.user import User

router = APIRouter(prefix="/workouts", tags=["Workouts"])


# ---------- Muscle groups ----------


@router.get("/muscle-groups", response_model=list[MuscleGroupResponse])
async def list_muscle_groups(handler: ListMuscleGroupsQueryHandler = Depends(get_list_muscle_groups_handler)):
    return await handler.handle(ListMuscleGroupsQuery())


@router.post("/muscle-groups", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_muscle_group(
    payload: CreateMuscleGroupRequest,
    handler: CreateMuscleGroupCommandHandler = Depends(get_create_muscle_group_handler),
    _: User = Depends(get_current_user),
):
    new_id = await handler.handle(CreateMuscleGroupCommand(name=payload.name))
    return IdResponse(id=new_id)


# ---------- Exercises ----------


@router.get("/exercises", response_model=ExerciseListResponse)
async def list_exercises(
    search: str | None = None,
    page: int = Query(default=DEFAULT_PAGE, ge=MIN_PAGE),
    size: int = Query(default=DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    handler: ListExercisesQueryHandler = Depends(get_list_exercises_handler),
):
    return await handler.handle(ListExercisesQuery(search=search, page=page, size=size))


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    handler: GetExerciseQueryHandler = Depends(get_get_exercise_handler),
):
    return await handler.handle(GetExerciseQuery(exercise_id=exercise_id))


@router.post("/exercises", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    payload: CreateExerciseRequest,
    handler: CreateExerciseCommandHandler = Depends(get_create_exercise_handler),
    _: User = Depends(get_current_user),
):
    new_id = await handler.handle(
        CreateExerciseCommand(
            name=payload.name,
            primary_muscle_group_id=payload.primary_muscle_group_id,
            secondary_muscle_group_ids=payload.secondary_muscle_group_ids,
        )
    )
    return IdResponse(id=new_id)


# ---------- Plans ----------


@router.get("/plans/public", response_model=WorkoutPlanListResponse)
async def list_public_plans(
    page: int = Query(default=DEFAULT_PAGE, ge=MIN_PAGE),
    size: int = Query(default=DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    handler: ListPublicPlansQueryHandler = Depends(get_list_public_plans_handler),
):
    return await handler.handle(ListPublicPlansQuery(page=page, size=size))


@router.get("/plans", response_model=WorkoutPlanListResponse)
async def list_my_plans(
    page: int = Query(default=DEFAULT_PAGE, ge=MIN_PAGE),
    size: int = Query(default=DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    handler: ListMyPlansQueryHandler = Depends(get_list_my_plans_handler),
    current_user: User = Depends(get_current_user),
):
    return await handler.handle(ListMyPlansQuery(user_id=current_user.id, page=page, size=size))


@router.post("/plans", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: CreateWorkoutPlanRequest,
    handler: CreateWorkoutPlanCommandHandler = Depends(get_create_workout_plan_handler),
    current_user: User = Depends(get_current_user),
):
    cmd = CreateWorkoutPlanCommand(
        author_id=current_user.id,
        title=payload.title,
        description=payload.description,
        is_public=payload.is_public,
        trainings=[
            PlanTrainingInput(
                name=t.name,
                order_num=t.order_num,
                weekday=t.weekday,
                exercises=[
                    PlanTrainingExerciseInput(
                        exercise_id=ex.exercise_id,
                        order_num=ex.order_num,
                        target_sets=ex.target_sets,
                        target_reps=ex.target_reps,
                        target_weight_pct=ex.target_weight_pct,
                    )
                    for ex in t.exercises
                ],
            )
            for t in payload.trainings
        ],
    )
    new_id = await handler.handle(cmd)
    return IdResponse(id=new_id)


@router.get("/plans/{plan_id}", response_model=PlanDetailResponse)
async def get_plan(
    plan_id: int,
    handler: GetPlanDetailQueryHandler = Depends(get_get_plan_detail_handler),
    current_user: User = Depends(get_current_user),
):
    return await handler.handle(GetPlanDetailQuery(plan_id=plan_id, viewer_id=current_user.id))


@router.put("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_plan(
    plan_id: int,
    payload: UpdateWorkoutPlanRequest,
    handler: UpdateWorkoutPlanCommandHandler = Depends(get_update_workout_plan_handler),
    current_user: User = Depends(get_current_user),
):
    await handler.handle(
        UpdateWorkoutPlanCommand(
            plan_id=plan_id,
            user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            is_public=payload.is_public,
        )
    )


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int,
    handler: DeleteWorkoutPlanCommandHandler = Depends(get_delete_workout_plan_handler),
    current_user: User = Depends(get_current_user),
):
    await handler.handle(DeleteWorkoutPlanCommand(plan_id=plan_id, user_id=current_user.id))


@router.post("/plans/{plan_id}/trainings", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def add_training(
    plan_id: int,
    payload: CreatePlanTrainingRequest,
    handler: AddTrainingCommandHandler = Depends(get_add_training_handler),
    current_user: User = Depends(get_current_user),
):
    new_id = await handler.handle(
        AddTrainingCommand(
            plan_id=plan_id,
            user_id=current_user.id,
            name=payload.name,
            weekday=payload.weekday,
            order_num=payload.order_num,
        )
    )
    return IdResponse(id=new_id)


@router.delete("/plans/{plan_id}/trainings/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training(
    plan_id: int,
    training_id: int,
    handler: DeleteTrainingCommandHandler = Depends(get_delete_training_handler),
    current_user: User = Depends(get_current_user),
):
    await handler.handle(
        DeleteTrainingCommand(
            plan_id=plan_id,
            training_id=training_id,
            user_id=current_user.id,
        )
    )


@router.post(
    "/plans/{plan_id}/trainings/{training_id}/exercises",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_exercise_to_training(
    plan_id: int,
    training_id: int,
    payload: AddExerciseToTrainingRequest,
    handler: AddExerciseToTrainingCommandHandler = Depends(get_add_exercise_to_training_handler),
    current_user: User = Depends(get_current_user),
):
    new_id = await handler.handle(
        AddExerciseToTrainingCommand(
            plan_id=plan_id,
            training_id=training_id,
            user_id=current_user.id,
            exercise_id=payload.exercise_id,
            order_num=payload.order_num,
            target_sets=payload.target_sets,
            target_reps=payload.target_reps,
            target_weight_pct=payload.target_weight_pct,
        )
    )
    return IdResponse(id=new_id)


@router.delete(
    "/plans/{plan_id}/trainings/{training_id}/exercises/{pte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_training_exercise(
    plan_id: int,
    training_id: int,
    pte_id: int,
    handler: DeleteTrainingExerciseCommandHandler = Depends(get_delete_training_exercise_handler),
    current_user: User = Depends(get_current_user),
):
    await handler.handle(
        DeleteTrainingExerciseCommand(
            plan_id=plan_id,
            training_id=training_id,
            pte_id=pte_id,
            user_id=current_user.id,
        )
    )


# ---------- Sessions ----------


@router.post("/sessions", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    payload: StartSessionRequest,
    handler: StartSessionCommandHandler = Depends(get_start_session_handler),
    current_user: User = Depends(get_current_user),
):
    new_id = await handler.handle(StartSessionCommand(user_id=current_user.id, plan_training_id=payload.plan_training_id))
    return IdResponse(id=new_id)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(default=DEFAULT_PAGE, ge=MIN_PAGE),
    size: int = Query(default=DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    handler: ListUserSessionsQueryHandler = Depends(get_list_user_sessions_handler),
    current_user: User = Depends(get_current_user),
):
    return await handler.handle(ListUserSessionsQuery(user_id=current_user.id, page=page, size=size))


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    handler: GetSessionDetailQueryHandler = Depends(get_get_session_detail_handler),
    current_user: User = Depends(get_current_user),
):
    return await handler.handle(GetSessionDetailQuery(session_id=session_id, user_id=current_user.id))


@router.patch("/sessions/{session_id}/end", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(
    session_id: int,
    handler: EndSessionCommandHandler = Depends(get_end_session_handler),
    current_user: User = Depends(get_current_user),
):
    await handler.handle(EndSessionCommand(session_id=session_id, user_id=current_user.id))


@router.post(
    "/sessions/{session_id}/exercises",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_exercise_to_session(
    session_id: int,
    payload: AddExerciseToSessionRequest,
    handler: AddExerciseToSessionCommandHandler = Depends(get_add_exercise_to_session_handler),
    current_user: User = Depends(get_current_user),
):
    new_id = await handler.handle(
        AddExerciseToSessionCommand(
            session_id=session_id,
            user_id=current_user.id,
            exercise_id=payload.exercise_id,
            order_num=payload.order_num,
        )
    )
    return IdResponse(id=new_id)


@router.post(
    "/sessions/{session_id}/exercises/{exercise_session_id}/sets",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_set(
    session_id: int,
    exercise_session_id: int,
    payload: LogSetRequest,
    handler: LogSetCommandHandler = Depends(get_log_set_handler),
    current_user: User = Depends(get_current_user),
):
    new_id = await handler.handle(
        LogSetCommand(
            session_id=session_id,
            exercise_session_id=exercise_session_id,
            user_id=current_user.id,
            set_number=payload.set_number,
            reps=payload.reps,
            weight=payload.weight,
        )
    )
    return IdResponse(id=new_id)


# ---------- Personal records ----------


@router.get("/personal-records", response_model=list[PersonalRecordResponse])
async def list_personal_records(
    handler: ListPersonalRecordsQueryHandler = Depends(get_list_personal_records_handler),
    current_user: User = Depends(get_current_user),
):
    return await handler.handle(ListPersonalRecordsQuery(user_id=current_user.id))


@router.post("/personal-records", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
async def upsert_personal_record(
    payload: UpsertPersonalRecordRequest,
    handler: UpsertPersonalRecordCommandHandler = Depends(get_upsert_personal_record_handler),
    current_user: User = Depends(get_current_user),
):
    new_id = await handler.handle(
        UpsertPersonalRecordCommand(
            user_id=current_user.id,
            exercise_id=payload.exercise_id,
            weight=payload.weight,
        )
    )
    return IdResponse(id=new_id)


@router.delete("/personal-records/{pr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personal_record(
    pr_id: int,
    handler: DeletePersonalRecordCommandHandler = Depends(get_delete_personal_record_handler),
    current_user: User = Depends(get_current_user),
):
    await handler.handle(DeletePersonalRecordCommand(pr_id=pr_id, user_id=current_user.id))
