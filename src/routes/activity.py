from fastapi import APIRouter, Depends, Query

from src.models.user import User
from src.routes.dependencies import get_activity_service, get_current_user
from src.schemas.activity import (
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
from src.services.activity import ActivityService

router = APIRouter(prefix="/workouts", tags=["Workouts"])


@router.get("/muscle-groups", response_model=list[MuscleGroupResponse])
async def list_muscle_groups(service: ActivityService = Depends(get_activity_service)):
    return await service.list_muscle_groups()


@router.post("/muscle-groups", response_model=MuscleGroupResponse, status_code=201)
async def create_muscle_group(
    payload: CreateMuscleGroupRequest,
    service: ActivityService = Depends(get_activity_service),
    _: User = Depends(get_current_user),
):
    return await service.create_muscle_group(payload)


@router.get("/exercises", response_model=ExerciseListResponse)
async def list_exercises(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: ActivityService = Depends(get_activity_service),
):
    return await service.list_exercises(search=search, page=page, size=size)


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(exercise_id: int, service: ActivityService = Depends(get_activity_service)):
    return await service.get_exercise(exercise_id)


@router.post("/exercises", response_model=ExerciseResponse, status_code=201)
async def create_exercise(
    payload: CreateExerciseRequest,
    service: ActivityService = Depends(get_activity_service),
    _: User = Depends(get_current_user),
):
    return await service.create_exercise(payload)


@router.get("/plans/public", response_model=WorkoutPlanListResponse)
async def list_public_plans(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: ActivityService = Depends(get_activity_service),
):
    return await service.list_public_plans(page=page, size=size)


@router.get("/plans", response_model=WorkoutPlanListResponse)
async def list_my_plans(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.list_user_plans(user_id=current_user.id, page=page, size=size)


@router.post("/plans", response_model=PlanDetailResponse, status_code=201)
async def create_plan(
    payload: CreateWorkoutPlanRequest,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.create_plan(user_id=current_user.id, payload=payload)


@router.get("/plans/{plan_id}", response_model=PlanDetailResponse)
async def get_plan(
    plan_id: int,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.get_plan(plan_id=plan_id, requesting_user_id=current_user.id)


@router.put("/plans/{plan_id}", response_model=WorkoutPlanResponse)
async def update_plan(
    plan_id: int,
    payload: UpdateWorkoutPlanRequest,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.update_plan(plan_id=plan_id, user_id=current_user.id, payload=payload)


@router.delete("/plans/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: int,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    await service.delete_plan(plan_id=plan_id, user_id=current_user.id)


@router.post("/plans/{plan_id}/trainings", response_model=PlanTrainingResponse, status_code=201)
async def add_training(
    plan_id: int,
    payload: CreatePlanTrainingRequest,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.add_training(plan_id=plan_id, user_id=current_user.id, payload=payload)


@router.delete("/plans/{plan_id}/trainings/{training_id}", status_code=204)
async def delete_training(
    plan_id: int,
    training_id: int,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    await service.delete_training(plan_id=plan_id, training_id=training_id, user_id=current_user.id)


@router.post("/plans/{plan_id}/trainings/{training_id}/exercises", response_model=PlanTrainingExerciseResponse, status_code=201)
async def add_exercise_to_training(
    plan_id: int,
    training_id: int,
    payload: AddExerciseToTrainingRequest,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.add_exercise_to_training(plan_id=plan_id, training_id=training_id, user_id=current_user.id, payload=payload)


@router.delete("/plans/{plan_id}/trainings/{training_id}/exercises/{pte_id}", status_code=204)
async def delete_training_exercise(
    plan_id: int,
    training_id: int,
    pte_id: int,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    await service.delete_training_exercise(plan_id=plan_id, training_id=training_id, pte_id=pte_id, user_id=current_user.id)


@router.post("/sessions", response_model=WorkoutSessionResponse, status_code=201)
async def start_session(
    payload: StartSessionRequest,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.start_session(user_id=current_user.id, payload=payload)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.list_user_sessions(user_id=current_user.id, page=page, size=size)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.get_session_detail(session_id=session_id, user_id=current_user.id)


@router.patch("/sessions/{session_id}/end", response_model=WorkoutSessionResponse)
async def end_session(
    session_id: int,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.end_session(session_id=session_id, user_id=current_user.id)


@router.post("/sessions/{session_id}/exercises", response_model=ExerciseSessionResponse, status_code=201)
async def add_exercise_to_session(
    session_id: int,
    payload: AddExerciseToSessionRequest,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.add_exercise_to_session(session_id=session_id, user_id=current_user.id, payload=payload)


@router.post("/sessions/{session_id}/exercises/{exercise_session_id}/sets", response_model=WorkoutSetResponse, status_code=201)
async def add_set(
    session_id: int,
    exercise_session_id: int,
    payload: LogSetRequest,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.add_set(session_id=session_id, exercise_session_id=exercise_session_id, user_id=current_user.id, payload=payload)


@router.get("/personal-records", response_model=list[PersonalRecordResponse])
async def list_personal_records(
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.list_personal_records(user_id=current_user.id)


@router.post("/personal-records", response_model=PersonalRecordResponse, status_code=201)
async def upsert_personal_record(
    payload: UpsertPersonalRecordRequest,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.upsert_personal_record(user_id=current_user.id, payload=payload)


@router.delete("/personal-records/{pr_id}", response_model=DeletePersonalRecordResponse)
async def delete_personal_record(
    pr_id: int,
    service: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user),
):
    return await service.delete_personal_record(pr_id=pr_id, user_id=current_user.id)
