from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

from src.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, NotResourceOwnerError, SessionAlreadyEndedError
from src.models.activity import Exercise, ExerciseSession, PlanTraining, WorkoutPlan, WorkoutSession
from src.repositories.activity import ActivityRepository
from src.repositories.activity_uow import ActivityUnitOfWork
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


class ActivityService:
    def __init__(self, uow: ActivityUnitOfWork):
        self.uow = uow

    @property
    def repo(self) -> ActivityRepository:
        return self.uow.repo

    async def list_muscle_groups(self) -> list[MuscleGroupResponse]:
        groups = await self.repo.list_muscle_groups()
        return _build_muscle_group_list_response(groups)

    async def create_muscle_group(self, payload: CreateMuscleGroupRequest) -> MuscleGroupResponse:
        async with self.uow:
            mg = await self.repo.create_muscle_group(payload.name.strip())
        return _build_muscle_group_response(mg)

    async def list_exercises(self, search: str | None, page: int, size: int) -> ExerciseListResponse:
        offset = (page - 1) * size
        items, total = await self.repo.list_exercises(search=search, offset=offset, limit=size)
        return _build_exercise_list_response(items, total, page, size)

    async def get_exercise(self, exercise_id: int) -> ExerciseResponse:
        exercise = await self.repo.get_exercise_by_id(exercise_id)
        if exercise is None:
            raise NotFoundError(resource="Exercise", resource_id=exercise_id)
        return _build_exercise_response(exercise)

    async def create_exercise(self, payload: CreateExerciseRequest) -> ExerciseResponse:
        async with self.uow:
            if payload.primary_muscle_group_id is not None:
                mg = await self.repo.get_muscle_group_by_id(payload.primary_muscle_group_id)
                if mg is None:
                    raise NotFoundError(resource="MuscleGroup", resource_id=payload.primary_muscle_group_id)

            for mg_id in payload.secondary_muscle_group_ids:
                mg = await self.repo.get_muscle_group_by_id(mg_id)
                if mg is None:
                    raise NotFoundError(resource="MuscleGroup", resource_id=mg_id)

            exercise = await self.repo.create_exercise(payload.name.strip(), payload.primary_muscle_group_id, payload.secondary_muscle_group_ids)

        full = await self.repo.get_exercise_by_id(exercise.id)
        return _build_exercise_response(full)

    async def list_public_plans(self, page: int, size: int) -> WorkoutPlanListResponse:
        offset = (page - 1) * size
        items, total = await self.repo.list_public_plans(offset=offset, limit=size)
        return _build_workout_plan_list_response(items, total, page, size)

    async def list_user_plans(self, user_id: int, page: int, size: int) -> WorkoutPlanListResponse:
        offset = (page - 1) * size
        items, total = await self.repo.list_user_plans(user_id=user_id, offset=offset, limit=size)
        return _build_workout_plan_list_response(items, total, page, size)

    async def get_plan(self, plan_id: int, requesting_user_id: int) -> PlanDetailResponse:
        plan = await self.repo.get_plan_with_trainings(plan_id)
        if plan is None:
            raise NotFoundError(resource="WorkoutPlan", resource_id=plan_id)
        if not plan.is_public and plan.author_id != requesting_user_id:
            raise ForbiddenError(message="This workout plan is private")
        return _build_plan_detail_response(plan)

    async def create_plan(self, user_id: int, payload: CreateWorkoutPlanRequest) -> PlanDetailResponse:
        async with self.uow:
            plan = await self.repo.create_plan(author_id=user_id, title=payload.title, description=payload.description, is_public=payload.is_public)

            for t in payload.trainings:
                for ex in t.exercises:
                    exercise = await self.repo.get_exercise_by_id(ex.exercise_id)
                    if exercise is None:
                        raise NotFoundError(resource="Exercise", resource_id=ex.exercise_id)

                training = await self.repo.add_training(plan_id=plan.id, name=t.name, weekday=t.weekday, order_num=t.order_num)
                for ex in t.exercises:
                    await self.repo.add_exercise_to_training(
                        plan_training_id=training.id,
                        exercise_id=ex.exercise_id,
                        order_num=ex.order_num,
                        target_sets=ex.target_sets,
                        target_reps=ex.target_reps,
                        target_weight_pct=ex.target_weight_pct,
                    )

        full = await self.repo.get_plan_with_trainings(plan.id)
        return _build_plan_detail_response(full)

    async def update_plan(self, plan_id: int, user_id: int, payload: UpdateWorkoutPlanRequest) -> WorkoutPlanResponse:
        async with self.uow:
            plan = await self.repo.get_plan_by_id(plan_id)
            if plan is None:
                raise NotFoundError(resource="WorkoutPlan", resource_id=plan_id)
            if plan.author_id != user_id:
                raise ForbiddenError(message="You do not own this workout plan")
            plan = await self.repo.update_plan(plan, **payload.model_dump(exclude_none=True))
        return _build_plan_response(plan)

    async def delete_plan(self, plan_id: int, user_id: int) -> None:
        async with self.uow:
            plan = await self.repo.get_plan_by_id(plan_id)
            if plan is None:
                raise NotFoundError(resource="WorkoutPlan", resource_id=plan_id)
            if plan.author_id != user_id:
                raise ForbiddenError(message="You do not own this workout plan")
            await self.repo.delete_plan(plan)

    async def add_training(self, plan_id: int, user_id: int, payload: CreatePlanTrainingRequest) -> PlanTrainingResponse:
        async with self.uow:
            plan = await self.repo.get_plan_by_id(plan_id)
            if plan is None:
                raise NotFoundError(resource="WorkoutPlan", resource_id=plan_id)
            if plan.author_id != user_id:
                raise ForbiddenError(message="You do not own this workout plan")
            training = await self.repo.add_training(plan_id=plan_id, name=payload.name, weekday=payload.weekday, order_num=payload.order_num)

        full = await self.repo.get_training_with_exercises(training.id)
        return _build_training_response(full)

    async def delete_training(self, plan_id: int, training_id: int, user_id: int) -> None:
        async with self.uow:
            plan = await self.repo.get_plan_by_id(plan_id)
            if plan is None:
                raise NotFoundError(resource="WorkoutPlan", resource_id=plan_id)
            if plan.author_id != user_id:
                raise ForbiddenError(message="You do not own this workout plan")
            training = await self.repo.get_training_by_id(training_id)
            if training is None or training.plan_id != plan_id:
                raise NotFoundError(resource="PlanTraining", resource_id=training_id)
            await self.repo.delete_training(training)

    async def add_exercise_to_training(
        self, plan_id: int, training_id: int, user_id: int, payload: AddExerciseToTrainingRequest
    ) -> PlanTrainingExerciseResponse:
        async with self.uow:
            plan = await self.repo.get_plan_by_id(plan_id)
            if plan is None:
                raise NotFoundError(resource="WorkoutPlan", resource_id=plan_id)
            if plan.author_id != user_id:
                raise ForbiddenError(message="You do not own this workout plan")

            training = await self.repo.get_training_by_id(training_id)
            if training is None or training.plan_id != plan_id:
                raise NotFoundError(resource="PlanTraining", resource_id=training_id)

            exercise = await self.repo.get_exercise_by_id(payload.exercise_id)
            if exercise is None:
                raise NotFoundError(resource="Exercise", resource_id=payload.exercise_id)

            pte = await self.repo.add_exercise_to_training(
                plan_training_id=training_id,
                exercise_id=payload.exercise_id,
                order_num=payload.order_num,
                target_sets=payload.target_sets,
                target_reps=payload.target_reps,
                target_weight_pct=payload.target_weight_pct,
            )

        return _build_training_exercise_response(pte)

    async def delete_training_exercise(self, plan_id: int, training_id: int, pte_id: int, user_id: int) -> None:
        async with self.uow:
            plan = await self.repo.get_plan_by_id(plan_id)
            if plan is None:
                raise NotFoundError(resource="WorkoutPlan", resource_id=plan_id)
            if plan.author_id != user_id:
                raise ForbiddenError(message="You do not own this workout plan")

            training = await self.repo.get_training_by_id(training_id)
            if training is None or training.plan_id != plan_id:
                raise NotFoundError(resource="PlanTraining", resource_id=training_id)

            pte = await self.repo.get_training_exercise_by_id(pte_id)
            if pte is None or pte.plan_training_id != training_id:
                raise NotFoundError(resource="PlanTrainingExercise", resource_id=pte_id)

            await self.repo.delete_training_exercise(pte)

    async def start_session(self, user_id: int, payload: StartSessionRequest) -> WorkoutSessionResponse:
        async with self.uow:
            training: PlanTraining | None = None

            if payload.plan_training_id is not None:
                training = await self.repo.get_training_with_exercises(payload.plan_training_id)
                if training is None:
                    raise NotFoundError(resource="PlanTraining", resource_id=payload.plan_training_id)

                plan = await self.repo.get_plan_by_id(training.plan_id)
                if not plan.is_public and plan.author_id != user_id:
                    raise ForbiddenError(message="This training belongs to a private plan")

            session = await self.repo.create_session(user_id=user_id, plan_training_id=payload.plan_training_id)

            if training is not None:
                for pte in sorted(training.exercises, key=lambda x: x.order_num):
                    await self.repo.add_exercise_to_session(
                        workout_session_id=session.id,
                        exercise_id=pte.exercise_id,
                        order_num=pte.order_num,
                        is_from_template=True,
                    )

        return _build_session_response(session)

    async def end_session(self, session_id: int, user_id: int) -> WorkoutSessionResponse:
        async with self.uow:
            session = await self.repo.get_session_by_id(session_id)
            if session is None:
                raise NotFoundError(resource="WorkoutSession", resource_id=session_id)
            if session.user_id != user_id:
                raise NotResourceOwnerError(message="You do not own this session")
            if session.ended_at is not None:
                raise SessionAlreadyEndedError()
            session = await self.repo.end_session(session)

        return _build_session_response(session)

    async def get_session_detail(self, session_id: int, user_id: int) -> SessionDetailResponse:
        session = await self.repo.get_session_with_exercises(session_id)
        if session is None:
            raise NotFoundError(resource="WorkoutSession", resource_id=session_id)
        if session.user_id != user_id:
            raise ForbiddenError(message="You do not own this session")

        return _build_session_detail_response(session)

    async def list_user_sessions(self, user_id: int, page: int, size: int) -> SessionListResponse:
        offset = (page - 1) * size
        items, total = await self.repo.list_user_sessions(user_id=user_id, offset=offset, limit=size)
        return _build_session_list_response(items, total, page, size)

    async def add_exercise_to_session(self, session_id: int, user_id: int, payload: AddExerciseToSessionRequest) -> ExerciseSessionResponse:
        async with self.uow:
            session = await self.repo.get_session_by_id(session_id)
            if session is None:
                raise NotFoundError(resource="WorkoutSession", resource_id=session_id)
            if session.user_id != user_id:
                raise NotResourceOwnerError(message="You do not own this session")
            if session.ended_at is not None:
                raise SessionAlreadyEndedError(message="Cannot add exercises to an ended session")

            exercise = await self.repo.get_exercise_by_id(payload.exercise_id)
            if exercise is None:
                raise NotFoundError(resource="Exercise", resource_id=payload.exercise_id)

            es = await self.repo.add_exercise_to_session(
                workout_session_id=session_id,
                exercise_id=payload.exercise_id,
                order_num=payload.order_num,
                is_from_template=False,
            )

        return _build_exercise_session_response(es, exercise)

    async def add_set(self, session_id: int, exercise_session_id: int, user_id: int, payload: LogSetRequest) -> WorkoutSetResponse:
        async with self.uow:
            session = await self.repo.get_session_by_id(session_id)
            if session is None:
                raise NotFoundError(resource="WorkoutSession", resource_id=session_id)
            if session.user_id != user_id:
                raise NotResourceOwnerError(message="You do not own this session")
            if session.ended_at is not None:
                raise SessionAlreadyEndedError(message="Cannot log sets on an ended session")

            es = await self.repo.get_exercise_session_by_id(exercise_session_id)
            if es is None or es.workout_session_id != session_id:
                raise NotFoundError(resource="ExerciseSession", resource_id=exercise_session_id)

            ws = await self.repo.add_set(
                exercise_session_id=exercise_session_id,
                set_number=payload.set_number,
                reps=payload.reps,
                weight=payload.weight,
            )

            if payload.weight > 0:
                existing_pr = await self.repo.get_personal_record(user_id, es.exercise_id)
                if existing_pr is None or payload.weight > existing_pr.weight:
                    await self.repo.upsert_personal_record(user_id=user_id, exercise_id=es.exercise_id, weight=payload.weight)

        return _build_workout_set_response(ws)

    async def list_personal_records(self, user_id: int) -> list[PersonalRecordResponse]:
        records = await self.repo.list_user_personal_records(user_id)
        return [_build_pr_response(pr) for pr in records]

    async def upsert_personal_record(self, user_id: int, payload: UpsertPersonalRecordRequest) -> PersonalRecordResponse:
        async with self.uow:
            exercise = await self.repo.get_exercise_by_id(payload.exercise_id)
            if exercise is None:
                raise NotFoundError(resource="Exercise", resource_id=payload.exercise_id)

            existing = await self.repo.get_personal_record(user_id, payload.exercise_id)
            if existing is not None and payload.weight < existing.weight:
                raise BadRequestError(message=f"New weight {payload.weight} kg is less than current record {existing.weight} kg")

            pr = await self.repo.upsert_personal_record(user_id=user_id, exercise_id=payload.exercise_id, weight=payload.weight)

        records = await self.repo.list_user_personal_records(user_id)
        for r in records:
            if r.id == pr.id:
                return _build_pr_response(r)
        return _build_pr_response(pr)

    async def delete_personal_record(self, pr_id: int, user_id: int) -> DeletePersonalRecordResponse:
        async with self.uow:
            pr = await self.repo.get_personal_record_by_id(pr_id)
            if pr is None:
                raise NotFoundError(resource="PersonalRecord", resource_id=pr_id)
            if pr.user_id != user_id:
                raise NotResourceOwnerError(message="You do not own this personal record")
            await self.repo.delete_personal_record(pr)
        return _build_delete_personal_record_response(pr_id)


def _session_duration_minutes(session: WorkoutSession) -> float | None:
    if session.ended_at is None:
        return None
    delta = session.ended_at - session.started_at
    return round(delta.total_seconds() / 60, 2)


def _build_session_response(session: WorkoutSession) -> WorkoutSessionResponse:
    return WorkoutSessionResponse(
        id=session.id,
        user_id=session.user_id,
        plan_training_id=session.plan_training_id,
        started_at=session.started_at.isoformat(),
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
        duration_minutes=_session_duration_minutes(session),
    )


def _build_exercise_session_response(es: ExerciseSession, exercise: Exercise) -> ExerciseSessionResponse:
    try:
        unloaded = sa_inspect(es).unloaded
        sets = [] if "sets" in unloaded else es.sets
    except NoInspectionAvailable:
        sets = getattr(es, "sets", [])

    return ExerciseSessionResponse(
        id=es.id,
        exercise_id=es.exercise_id,
        exercise_name=exercise.name,
        order_num=es.order_num,
        is_from_template=es.is_from_template,
        sets=[WorkoutSetResponse(id=s.id, set_number=s.set_number, reps=s.reps, weight=s.weight) for s in sets],
    )


def _build_exercise_response(exercise: Exercise) -> ExerciseResponse:
    secondary = [MuscleGroupResponse(id=link.muscle_group.id, name=link.muscle_group.name) for link in exercise.secondary_muscle_group_links]
    return ExerciseResponse(
        id=exercise.id,
        name=exercise.name,
        primary_muscle_group=MuscleGroupResponse(id=exercise.primary_muscle_group.id, name=exercise.primary_muscle_group.name)
        if exercise.primary_muscle_group
        else None,
        secondary_muscle_groups=secondary,
    )


def _build_training_exercise_response(pte) -> PlanTrainingExerciseResponse:
    return PlanTrainingExerciseResponse(
        id=pte.id,
        exercise_id=pte.exercise_id,
        exercise_name=pte.exercise.name,
        order_num=pte.order_num,
        target_sets=pte.target_sets,
        target_reps=pte.target_reps,
        target_weight_pct=pte.target_weight_pct,
    )


def _build_plan_detail_response(plan: WorkoutPlan) -> PlanDetailResponse:
    return PlanDetailResponse(
        id=plan.id,
        author_id=plan.author_id,
        title=plan.title,
        description=plan.description,
        is_public=plan.is_public,
        trainings=[_build_training_response(t) for t in sorted(plan.trainings, key=lambda x: x.order_num)],
    )


def _build_training_response(training: PlanTraining) -> PlanTrainingResponse:
    return PlanTrainingResponse(
        id=training.id,
        plan_id=training.plan_id,
        name=training.name,
        weekday=training.weekday.value if training.weekday else None,
        order_num=training.order_num,
        exercises=[_build_training_exercise_response(pte) for pte in sorted(training.exercises, key=lambda x: x.order_num)],
    )


def _build_plan_response(plan: WorkoutPlan) -> WorkoutPlanResponse:
    return WorkoutPlanResponse(
        id=plan.id,
        author_id=plan.author_id,
        title=plan.title,
        description=plan.description,
        is_public=plan.is_public,
    )


def _build_pr_response(pr) -> PersonalRecordResponse:
    return PersonalRecordResponse(
        id=pr.id,
        user_id=pr.user_id,
        exercise_id=pr.exercise_id,
        exercise_name=pr.exercise.name,
        weight=pr.weight,
        recorded_at=pr.recorded_at.isoformat(),
    )


def _build_session_detail_response(session: WorkoutSession) -> SessionDetailResponse:
    exercise_sessions = [_build_exercise_session_response(es, es.exercise) for es in sorted(session.exercise_sessions, key=lambda x: x.order_num)]
    return SessionDetailResponse(
        id=session.id,
        user_id=session.user_id,
        plan_training_id=session.plan_training_id,
        started_at=session.started_at.isoformat(),
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
        duration_minutes=_session_duration_minutes(session),
        exercise_sessions=exercise_sessions,
    )


def _build_muscle_group_response(mg) -> MuscleGroupResponse:
    return MuscleGroupResponse(id=mg.id, name=mg.name)


def _build_muscle_group_list_response(mgs) -> list[MuscleGroupResponse]:
    return [_build_muscle_group_response(mg) for mg in mgs]


def _build_workout_plan_list_response(plans, total, page, size) -> WorkoutPlanListResponse:
    return WorkoutPlanListResponse(
        items=[_build_plan_response(p) for p in plans],
        total=total,
        page=page,
        size=size,
    )


def _build_workout_set_response(ws) -> WorkoutSetResponse:
    return WorkoutSetResponse(id=ws.id, set_number=ws.set_number, reps=ws.reps, weight=ws.weight)


def _build_session_list_response(sessions, total, page, size) -> SessionListResponse:
    return SessionListResponse(
        items=[_build_session_response(s) for s in sessions],
        total=total,
        page=page,
        size=size,
    )


def _build_exercise_list_response(exercises, total, page, size) -> ExerciseListResponse:
    return ExerciseListResponse(
        items=[_build_exercise_response(e) for e in exercises],
        total=total,
        page=page,
        size=size,
    )


def _build_delete_personal_record_response(pr_id: int) -> DeletePersonalRecordResponse:
    return DeletePersonalRecordResponse(deleted_pr_id=pr_id)
