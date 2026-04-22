from src.activity.application.dto import Page
from src.activity.domain.models import (
    ExerciseDomain,
    ExerciseSessionDomain,
    MuscleGroupDomain,
    PersonalRecordDomain,
    PlanTrainingDomain,
    PlanTrainingExerciseDomain,
    WorkoutPlanDomain,
    WorkoutSessionDomain,
    WorkoutSetDomain,
)
from src.activity.presentation.schemas import (
    DeletePersonalRecordResponse,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseSessionResponse,
    MuscleGroupResponse,
    PersonalRecordResponse,
    PlanDetailResponse,
    PlanTrainingExerciseResponse,
    PlanTrainingResponse,
    SessionDetailResponse,
    SessionListResponse,
    WorkoutPlanListResponse,
    WorkoutPlanResponse,
    WorkoutSessionResponse,
    WorkoutSetResponse,
)


def muscle_group_to_response(d: MuscleGroupDomain) -> MuscleGroupResponse:
    return MuscleGroupResponse(id=d.id, name=d.name)


def exercise_to_response(d: ExerciseDomain) -> ExerciseResponse:
    return ExerciseResponse(
        id=d.id,
        name=d.name,
        primary_muscle_group=muscle_group_to_response(d.primary_muscle_group) if d.primary_muscle_group else None,
        secondary_muscle_groups=[muscle_group_to_response(mg) for mg in d.secondary_muscle_groups],
    )


def exercise_page_to_response(page: Page[ExerciseDomain]) -> ExerciseListResponse:
    return ExerciseListResponse(
        items=[exercise_to_response(e) for e in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
    )


def plan_training_exercise_to_response(d: PlanTrainingExerciseDomain) -> PlanTrainingExerciseResponse:
    return PlanTrainingExerciseResponse(
        id=d.id,
        exercise_id=d.exercise_id,
        exercise_name=d.exercise_name or "",
        order_num=d.order_num,
        target_sets=d.target_sets,
        target_reps=d.target_reps,
        target_weight_pct=d.target_weight_pct,
    )


def plan_training_to_response(d: PlanTrainingDomain) -> PlanTrainingResponse:
    return PlanTrainingResponse(
        id=d.id,
        plan_id=d.plan_id,
        name=d.name,
        weekday=d.weekday,
        order_num=d.order_num,
        exercises=[plan_training_exercise_to_response(e) for e in d.exercises],
    )


def workout_plan_to_response(d: WorkoutPlanDomain) -> WorkoutPlanResponse:
    return WorkoutPlanResponse(
        id=d.id,
        author_id=d.author_id,
        title=d.title,
        description=d.description,
        is_public=d.is_public,
    )


def plan_detail_to_response(d: WorkoutPlanDomain) -> PlanDetailResponse:
    return PlanDetailResponse(
        id=d.id,
        author_id=d.author_id,
        title=d.title,
        description=d.description,
        is_public=d.is_public,
        trainings=[plan_training_to_response(t) for t in d.trainings],
    )


def workout_plan_page_to_response(page: Page[WorkoutPlanDomain]) -> WorkoutPlanListResponse:
    return WorkoutPlanListResponse(
        items=[workout_plan_to_response(p) for p in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
    )


def workout_set_to_response(d: WorkoutSetDomain) -> WorkoutSetResponse:
    return WorkoutSetResponse(
        id=d.id,
        set_number=d.set_number.value,
        reps=d.reps.value,
        weight=d.weight.value,
    )


def exercise_session_to_response(d: ExerciseSessionDomain) -> ExerciseSessionResponse:
    return ExerciseSessionResponse(
        id=d.id,
        exercise_id=d.exercise_id,
        exercise_name=d.exercise_name or "",
        order_num=d.order_num,
        is_from_template=d.is_from_template,
        sets=[workout_set_to_response(s) for s in d.sets],
    )


def workout_session_to_response(d: WorkoutSessionDomain) -> WorkoutSessionResponse:
    return WorkoutSessionResponse(
        id=d.id,
        user_id=d.user_id,
        plan_training_id=d.plan_training_id,
        started_at=d.started_at.isoformat(),
        ended_at=d.ended_at.isoformat() if d.ended_at else None,
        duration_minutes=d.duration_minutes(),
    )


def session_detail_to_response(d: WorkoutSessionDomain) -> SessionDetailResponse:
    return SessionDetailResponse(
        id=d.id,
        user_id=d.user_id,
        plan_training_id=d.plan_training_id,
        started_at=d.started_at.isoformat(),
        ended_at=d.ended_at.isoformat() if d.ended_at else None,
        duration_minutes=d.duration_minutes(),
        exercise_sessions=[exercise_session_to_response(es) for es in d.exercise_sessions],
    )


def session_page_to_response(page: Page[WorkoutSessionDomain]) -> SessionListResponse:
    return SessionListResponse(
        items=[workout_session_to_response(s) for s in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
    )


def personal_record_to_response(d: PersonalRecordDomain) -> PersonalRecordResponse:
    return PersonalRecordResponse(
        id=d.id,
        user_id=d.user_id,
        exercise_id=d.exercise_id,
        exercise_name=d.exercise_name or "",
        weight=d.weight.value,
        recorded_at=d.recorded_at.isoformat(),
    )


def delete_personal_record_to_response(pr_id: int) -> DeletePersonalRecordResponse:
    return DeletePersonalRecordResponse(deleted_pr_id=pr_id)
