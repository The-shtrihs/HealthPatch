from fastapi import APIRouter, Depends, Query, status

from src.activity.application.dto import (
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
    ListExercisesQuery,
    LogSetCommand,
    PlanTrainingExerciseInput,
    PlanTrainingInput,
    StartSessionCommand,
    UpdateWorkoutPlanCommand,
    UpsertPersonalRecordCommand,
)
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
from src.activity.presentation.dependencies import (
    get_add_exercise_to_session_uc,
    get_add_exercise_to_training_uc,
    get_add_training_uc,
    get_create_exercise_uc,
    get_create_muscle_group_uc,
    get_create_plan_uc,
    get_delete_personal_record_uc,
    get_delete_plan_uc,
    get_delete_training_exercise_uc,
    get_delete_training_uc,
    get_end_session_uc,
    get_get_exercise_uc,
    get_get_plan_uc,
    get_list_exercises_uc,
    get_list_muscle_groups_uc,
    get_list_personal_records_uc,
    get_list_public_plans_uc,
    get_list_user_plans_uc,
    get_list_user_sessions_uc,
    get_log_set_uc,
    get_session_detail_uc,
    get_start_session_uc,
    get_update_plan_uc,
    get_upsert_personal_record_uc,
)
from src.activity.presentation.response_builders import (
    delete_personal_record_to_response,
    exercise_page_to_response,
    exercise_session_to_response,
    exercise_to_response,
    muscle_group_to_response,
    personal_record_to_response,
    plan_detail_to_response,
    plan_training_exercise_to_response,
    plan_training_to_response,
    session_detail_to_response,
    session_page_to_response,
    workout_plan_page_to_response,
    workout_plan_to_response,
    workout_session_to_response,
    workout_set_to_response,
)
from src.activity.presentation.schemas import (
    AddExerciseToSessionRequest,
    AddExerciseToTrainingRequest,
    CreateExerciseRequest,
    CreateMuscleGroupRequest,
    CreatePlanTrainingRequest,
    CreateWorkoutPlanRequest,
    DeletePersonalRecordResponse,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseSessionResponse,
    LogSetRequest,
    MuscleGroupResponse,
    PersonalRecordResponse,
    PlanDetailResponse,
    PlanTrainingExerciseResponse,
    PlanTrainingResponse,
    SessionDetailResponse,
    SessionListResponse,
    StartSessionRequest,
    UpdateWorkoutPlanRequest,
    UpsertPersonalRecordRequest,
    WorkoutPlanListResponse,
    WorkoutPlanResponse,
    WorkoutSessionResponse,
    WorkoutSetResponse,
)
from src.auth.presentation.dependencies import get_current_user
from src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE, MIN_PAGE_SIZE
from src.models.user import User

router = APIRouter(prefix="/workouts", tags=["Workouts"])


# ---------- Muscle groups ----------


@router.get("/muscle-groups", response_model=list[MuscleGroupResponse])
async def list_muscle_groups(uc: ListMuscleGroupsUseCase = Depends(get_list_muscle_groups_uc)):
    groups = await uc.execute()
    return [muscle_group_to_response(g) for g in groups]


@router.post("/muscle-groups", response_model=MuscleGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_muscle_group(
    payload: CreateMuscleGroupRequest,
    uc: CreateMuscleGroupUseCase = Depends(get_create_muscle_group_uc),
    _: User = Depends(get_current_user),
):
    mg = await uc.execute(CreateMuscleGroupCommand(name=payload.name))
    return muscle_group_to_response(mg)


# ---------- Exercises ----------


@router.get("/exercises", response_model=ExerciseListResponse)
async def list_exercises(
    search: str | None = None,
    page: int = Query(default=DEFAULT_PAGE, ge=MIN_PAGE),
    size: int = Query(default=DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    uc: ListExercisesUseCase = Depends(get_list_exercises_uc),
):
    result = await uc.execute(ListExercisesQuery(search=search, page=page, size=size))
    return exercise_page_to_response(result)


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    uc: GetExerciseUseCase = Depends(get_get_exercise_uc),
):
    exercise = await uc.execute(exercise_id)
    return exercise_to_response(exercise)


@router.post("/exercises", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    payload: CreateExerciseRequest,
    uc: CreateExerciseUseCase = Depends(get_create_exercise_uc),
    _: User = Depends(get_current_user),
):
    exercise = await uc.execute(
        CreateExerciseCommand(
            name=payload.name,
            primary_muscle_group_id=payload.primary_muscle_group_id,
            secondary_muscle_group_ids=payload.secondary_muscle_group_ids,
        )
    )
    return exercise_to_response(exercise)


# ---------- Plans ----------


@router.get("/plans/public", response_model=WorkoutPlanListResponse)
async def list_public_plans(
    page: int = Query(default=DEFAULT_PAGE, ge=MIN_PAGE),
    size: int = Query(default=DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    uc: ListPublicPlansUseCase = Depends(get_list_public_plans_uc),
):
    result = await uc.execute(page=page, size=size)
    return workout_plan_page_to_response(result)


@router.get("/plans", response_model=WorkoutPlanListResponse)
async def list_my_plans(
    page: int = Query(default=DEFAULT_PAGE, ge=MIN_PAGE),
    size: int = Query(default=DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    uc: ListUserPlansUseCase = Depends(get_list_user_plans_uc),
    current_user: User = Depends(get_current_user),
):
    result = await uc.execute(user_id=current_user.id, page=page, size=size)
    return workout_plan_page_to_response(result)


@router.post("/plans", response_model=PlanDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: CreateWorkoutPlanRequest,
    uc: CreatePlanUseCase = Depends(get_create_plan_uc),
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
    plan = await uc.execute(cmd)
    return plan_detail_to_response(plan)


@router.get("/plans/{plan_id}", response_model=PlanDetailResponse)
async def get_plan(
    plan_id: int,
    uc: GetPlanUseCase = Depends(get_get_plan_uc),
    current_user: User = Depends(get_current_user),
):
    plan = await uc.execute(plan_id=plan_id, requesting_user_id=current_user.id)
    return plan_detail_to_response(plan)


@router.put("/plans/{plan_id}", response_model=WorkoutPlanResponse)
async def update_plan(
    plan_id: int,
    payload: UpdateWorkoutPlanRequest,
    uc: UpdatePlanUseCase = Depends(get_update_plan_uc),
    current_user: User = Depends(get_current_user),
):
    plan = await uc.execute(
        UpdateWorkoutPlanCommand(
            plan_id=plan_id,
            user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            is_public=payload.is_public,
        )
    )
    return workout_plan_to_response(plan)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int,
    uc: DeletePlanUseCase = Depends(get_delete_plan_uc),
    current_user: User = Depends(get_current_user),
):
    await uc.execute(DeleteWorkoutPlanCommand(plan_id=plan_id, user_id=current_user.id))


@router.post("/plans/{plan_id}/trainings", response_model=PlanTrainingResponse, status_code=status.HTTP_201_CREATED)
async def add_training(
    plan_id: int,
    payload: CreatePlanTrainingRequest,
    uc: AddTrainingUseCase = Depends(get_add_training_uc),
    current_user: User = Depends(get_current_user),
):
    training = await uc.execute(
        AddTrainingCommand(
            plan_id=plan_id,
            user_id=current_user.id,
            name=payload.name,
            weekday=payload.weekday,
            order_num=payload.order_num,
        )
    )
    return plan_training_to_response(training)


@router.delete("/plans/{plan_id}/trainings/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training(
    plan_id: int,
    training_id: int,
    uc: DeleteTrainingUseCase = Depends(get_delete_training_uc),
    current_user: User = Depends(get_current_user),
):
    await uc.execute(
        DeleteTrainingCommand(
            plan_id=plan_id,
            training_id=training_id,
            user_id=current_user.id,
        )
    )


@router.post(
    "/plans/{plan_id}/trainings/{training_id}/exercises",
    response_model=PlanTrainingExerciseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_exercise_to_training(
    plan_id: int,
    training_id: int,
    payload: AddExerciseToTrainingRequest,
    uc: AddExerciseToTrainingUseCase = Depends(get_add_exercise_to_training_uc),
    current_user: User = Depends(get_current_user),
):
    pte = await uc.execute(
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
    return plan_training_exercise_to_response(pte)


@router.delete(
    "/plans/{plan_id}/trainings/{training_id}/exercises/{pte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_training_exercise(
    plan_id: int,
    training_id: int,
    pte_id: int,
    uc: DeleteTrainingExerciseUseCase = Depends(get_delete_training_exercise_uc),
    current_user: User = Depends(get_current_user),
):
    await uc.execute(
        DeleteTrainingExerciseCommand(
            plan_id=plan_id,
            training_id=training_id,
            pte_id=pte_id,
            user_id=current_user.id,
        )
    )


# ---------- Sessions ----------


@router.post("/sessions", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    payload: StartSessionRequest,
    uc: StartSessionUseCase = Depends(get_start_session_uc),
    current_user: User = Depends(get_current_user),
):
    session = await uc.execute(StartSessionCommand(user_id=current_user.id, plan_training_id=payload.plan_training_id))
    return workout_session_to_response(session)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(default=DEFAULT_PAGE, ge=MIN_PAGE),
    size: int = Query(default=DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    uc: ListUserSessionsUseCase = Depends(get_list_user_sessions_uc),
    current_user: User = Depends(get_current_user),
):
    result = await uc.execute(user_id=current_user.id, page=page, size=size)
    return session_page_to_response(result)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    uc: GetSessionDetailUseCase = Depends(get_session_detail_uc),
    current_user: User = Depends(get_current_user),
):
    session = await uc.execute(session_id=session_id, user_id=current_user.id)
    return session_detail_to_response(session)


@router.patch("/sessions/{session_id}/end", response_model=WorkoutSessionResponse)
async def end_session(
    session_id: int,
    uc: EndSessionUseCase = Depends(get_end_session_uc),
    current_user: User = Depends(get_current_user),
):
    session = await uc.execute(EndSessionCommand(session_id=session_id, user_id=current_user.id))
    return workout_session_to_response(session)


@router.post(
    "/sessions/{session_id}/exercises",
    response_model=ExerciseSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_exercise_to_session(
    session_id: int,
    payload: AddExerciseToSessionRequest,
    uc: AddExerciseToSessionUseCase = Depends(get_add_exercise_to_session_uc),
    current_user: User = Depends(get_current_user),
):
    es = await uc.execute(
        AddExerciseToSessionCommand(
            session_id=session_id,
            user_id=current_user.id,
            exercise_id=payload.exercise_id,
            order_num=payload.order_num,
        )
    )
    return exercise_session_to_response(es)


@router.post(
    "/sessions/{session_id}/exercises/{exercise_session_id}/sets",
    response_model=WorkoutSetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_set(
    session_id: int,
    exercise_session_id: int,
    payload: LogSetRequest,
    uc: LogSetUseCase = Depends(get_log_set_uc),
    current_user: User = Depends(get_current_user),
):
    ws = await uc.execute(
        LogSetCommand(
            session_id=session_id,
            exercise_session_id=exercise_session_id,
            user_id=current_user.id,
            set_number=payload.set_number,
            reps=payload.reps,
            weight=payload.weight,
        )
    )
    return workout_set_to_response(ws)


# ---------- Personal records ----------


@router.get("/personal-records", response_model=list[PersonalRecordResponse])
async def list_personal_records(
    uc: ListPersonalRecordsUseCase = Depends(get_list_personal_records_uc),
    current_user: User = Depends(get_current_user),
):
    records = await uc.execute(current_user.id)
    return [personal_record_to_response(pr) for pr in records]


@router.post("/personal-records", response_model=PersonalRecordResponse, status_code=status.HTTP_201_CREATED)
async def upsert_personal_record(
    payload: UpsertPersonalRecordRequest,
    uc: UpsertPersonalRecordUseCase = Depends(get_upsert_personal_record_uc),
    current_user: User = Depends(get_current_user),
):
    pr = await uc.execute(
        UpsertPersonalRecordCommand(
            user_id=current_user.id,
            exercise_id=payload.exercise_id,
            weight=payload.weight,
        )
    )
    return personal_record_to_response(pr)


@router.delete("/personal-records/{pr_id}", response_model=DeletePersonalRecordResponse)
async def delete_personal_record(
    pr_id: int,
    uc: DeletePersonalRecordUseCase = Depends(get_delete_personal_record_uc),
    current_user: User = Depends(get_current_user),
):
    deleted_id = await uc.execute(DeletePersonalRecordCommand(pr_id=pr_id, user_id=current_user.id))
    return delete_personal_record_to_response(deleted_id)
