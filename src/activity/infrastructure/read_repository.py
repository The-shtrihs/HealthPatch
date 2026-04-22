from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.activity.application.read_models import (
    ExerciseReadModel,
    ExerciseSessionReadModel,
    MuscleGroupReadModel,
    PageReadModel,
    PersonalRecordReadModel,
    PlanTrainingExerciseReadModel,
    PlanTrainingReadModel,
    WorkoutPlanDetailReadModel,
    WorkoutPlanSummaryReadModel,
    WorkoutSessionDetailReadModel,
    WorkoutSessionSummaryReadModel,
    WorkoutSetReadModel,
)
from src.models.activity import (
    Exercise,
    ExerciseMuscleGroup,
    ExerciseSession,
    MuscleGroup,
    PersonalRecord,
    PlanTraining,
    PlanTrainingExercise,
    WorkoutPlan,
    WorkoutSession,
)


def _mg_to_rm(orm: MuscleGroup) -> MuscleGroupReadModel:
    return MuscleGroupReadModel(id=orm.id, name=orm.name)


def _exercise_to_rm(orm: Exercise) -> ExerciseReadModel:
    primary = _mg_to_rm(orm.primary_muscle_group) if orm.primary_muscle_group else None
    secondary = [_mg_to_rm(link.muscle_group) for link in orm.secondary_muscle_group_links]
    return ExerciseReadModel(
        id=orm.id,
        name=orm.name,
        primary_muscle_group=primary,
        secondary_muscle_groups=secondary,
    )


def _pte_to_rm(orm: PlanTrainingExercise) -> PlanTrainingExerciseReadModel:
    return PlanTrainingExerciseReadModel(
        id=orm.id,
        exercise_id=orm.exercise_id,
        exercise_name=orm.exercise.name if orm.exercise else "",
        order_num=orm.order_num,
        target_sets=orm.target_sets,
        target_reps=orm.target_reps,
        target_weight_pct=orm.target_weight_pct,
    )


def _training_to_rm(orm: PlanTraining) -> PlanTrainingReadModel:
    exercises = sorted(orm.exercises, key=lambda e: e.order_num)
    return PlanTrainingReadModel(
        id=orm.id,
        plan_id=orm.plan_id,
        name=orm.name,
        weekday=orm.weekday,
        order_num=orm.order_num,
        exercises=[_pte_to_rm(e) for e in exercises],
    )


def _plan_summary_to_rm(orm: WorkoutPlan) -> WorkoutPlanSummaryReadModel:
    return WorkoutPlanSummaryReadModel(
        id=orm.id,
        author_id=orm.author_id,
        title=orm.title,
        description=orm.description,
        is_public=orm.is_public,
    )


def _plan_detail_to_rm(orm: WorkoutPlan) -> WorkoutPlanDetailReadModel:
    trainings = sorted(orm.trainings, key=lambda t: t.order_num)
    return WorkoutPlanDetailReadModel(
        id=orm.id,
        author_id=orm.author_id,
        title=orm.title,
        description=orm.description,
        is_public=orm.is_public,
        trainings=[_training_to_rm(t) for t in trainings],
    )


def _duration_minutes(started_at, ended_at) -> float | None:
    if ended_at is None:
        return None
    return (ended_at - started_at).total_seconds() / 60.0


def _session_summary_to_rm(orm: WorkoutSession) -> WorkoutSessionSummaryReadModel:
    return WorkoutSessionSummaryReadModel(
        id=orm.id,
        user_id=orm.user_id,
        plan_training_id=orm.plan_training_id,
        started_at=orm.started_at,
        ended_at=orm.ended_at,
        duration_minutes=_duration_minutes(orm.started_at, orm.ended_at),
    )


def _set_to_rm(orm) -> WorkoutSetReadModel:
    return WorkoutSetReadModel(
        id=orm.id,
        set_number=orm.set_number,
        reps=orm.reps,
        weight=orm.weight,
    )


def _exercise_session_to_rm(orm: ExerciseSession) -> ExerciseSessionReadModel:
    sets = sorted(orm.sets, key=lambda s: s.set_number)
    return ExerciseSessionReadModel(
        id=orm.id,
        exercise_id=orm.exercise_id,
        exercise_name=orm.exercise.name if orm.exercise else "",
        order_num=orm.order_num,
        is_from_template=orm.is_from_template,
        sets=[_set_to_rm(s) for s in sets],
    )


def _session_detail_to_rm(orm: WorkoutSession) -> WorkoutSessionDetailReadModel:
    exercises = sorted(orm.exercise_sessions, key=lambda es: es.order_num)
    return WorkoutSessionDetailReadModel(
        id=orm.id,
        user_id=orm.user_id,
        plan_training_id=orm.plan_training_id,
        started_at=orm.started_at,
        ended_at=orm.ended_at,
        duration_minutes=_duration_minutes(orm.started_at, orm.ended_at),
        exercise_sessions=[_exercise_session_to_rm(es) for es in exercises],
    )


def _pr_to_rm(orm: PersonalRecord) -> PersonalRecordReadModel:
    return PersonalRecordReadModel(
        id=orm.id,
        user_id=orm.user_id,
        exercise_id=orm.exercise_id,
        exercise_name=orm.exercise.name if orm.exercise else "",
        weight=orm.weight,
        recorded_at=orm.recorded_at,
    )


class SqlAlchemyActivityReadRepository:
    """Read-side repository. Bypasses the domain layer; returns Read Models directly."""

    def __init__(self, session: AsyncSession):
        self._db = session

    # ---------- Muscle groups ----------

    async def list_muscle_groups(self) -> list[MuscleGroupReadModel]:
        result = await self._db.scalars(select(MuscleGroup).order_by(MuscleGroup.name))
        return [_mg_to_rm(mg) for mg in result.all()]

    # ---------- Exercises ----------

    async def get_exercise(self, exercise_id: int) -> ExerciseReadModel | None:
        result = await self._db.scalars(
            select(Exercise)
            .options(
                selectinload(Exercise.primary_muscle_group),
                selectinload(Exercise.secondary_muscle_group_links).selectinload(ExerciseMuscleGroup.muscle_group),
            )
            .where(Exercise.id == exercise_id)
        )
        orm = result.first()
        return _exercise_to_rm(orm) if orm else None

    async def list_exercises(
        self,
        search: str | None,
        offset: int,
        limit: int,
        page: int,
        size: int,
    ) -> PageReadModel[ExerciseReadModel]:
        query = select(Exercise).options(
            selectinload(Exercise.primary_muscle_group),
            selectinload(Exercise.secondary_muscle_group_links).selectinload(ExerciseMuscleGroup.muscle_group),
        )
        count_query = select(func.count()).select_from(Exercise)
        if search:
            pattern = f"%{search}%"
            query = query.where(Exercise.name.ilike(pattern))
            count_query = count_query.where(Exercise.name.ilike(pattern))

        total = (await self._db.scalar(count_query)) or 0
        items = list((await self._db.scalars(query.offset(offset).limit(limit).order_by(Exercise.name))).all())
        return PageReadModel(
            items=[_exercise_to_rm(e) for e in items],
            total=total,
            page=page,
            size=size,
        )

    # ---------- Workout plans ----------

    async def list_public_plans(self, offset: int, limit: int, page: int, size: int) -> PageReadModel[WorkoutPlanSummaryReadModel]:
        base = select(WorkoutPlan).where(WorkoutPlan.is_public.is_(True))
        total = (await self._db.scalar(select(func.count()).select_from(WorkoutPlan).where(WorkoutPlan.is_public.is_(True)))) or 0
        items = list((await self._db.scalars(base.offset(offset).limit(limit).order_by(WorkoutPlan.id.desc()))).all())
        return PageReadModel(
            items=[_plan_summary_to_rm(p) for p in items],
            total=total,
            page=page,
            size=size,
        )

    async def list_user_plans(
        self,
        user_id: int,
        offset: int,
        limit: int,
        page: int,
        size: int,
    ) -> PageReadModel[WorkoutPlanSummaryReadModel]:
        base = select(WorkoutPlan).where(WorkoutPlan.author_id == user_id)
        total = (await self._db.scalar(select(func.count()).select_from(WorkoutPlan).where(WorkoutPlan.author_id == user_id))) or 0
        items = list((await self._db.scalars(base.offset(offset).limit(limit).order_by(WorkoutPlan.id.desc()))).all())
        return PageReadModel(
            items=[_plan_summary_to_rm(p) for p in items],
            total=total,
            page=page,
            size=size,
        )

    async def get_plan_detail(self, plan_id: int) -> WorkoutPlanDetailReadModel | None:
        result = await self._db.scalars(
            select(WorkoutPlan)
            .options(selectinload(WorkoutPlan.trainings).selectinload(PlanTraining.exercises).selectinload(PlanTrainingExercise.exercise))
            .where(WorkoutPlan.id == plan_id)
        )
        orm = result.first()
        return _plan_detail_to_rm(orm) if orm else None

    async def get_plan_visibility(self, plan_id: int) -> tuple[int, bool] | None:
        """Returns (author_id, is_public) for visibility checks without loading the aggregate."""
        result = await self._db.execute(select(WorkoutPlan.author_id, WorkoutPlan.is_public).where(WorkoutPlan.id == plan_id))
        row = result.first()
        return (row.author_id, row.is_public) if row else None

    # ---------- Workout sessions ----------

    async def list_user_sessions(
        self,
        user_id: int,
        offset: int,
        limit: int,
        page: int,
        size: int,
    ) -> PageReadModel[WorkoutSessionSummaryReadModel]:
        base = select(WorkoutSession).where(WorkoutSession.user_id == user_id)
        total = (await self._db.scalar(select(func.count()).select_from(WorkoutSession).where(WorkoutSession.user_id == user_id))) or 0
        items = list((await self._db.scalars(base.offset(offset).limit(limit).order_by(WorkoutSession.started_at.desc()))).all())
        return PageReadModel(
            items=[_session_summary_to_rm(s) for s in items],
            total=total,
            page=page,
            size=size,
        )

    async def get_session_detail(self, session_id: int) -> WorkoutSessionDetailReadModel | None:
        result = await self._db.scalars(
            select(WorkoutSession)
            .options(
                selectinload(WorkoutSession.exercise_sessions).selectinload(ExerciseSession.sets),
                selectinload(WorkoutSession.exercise_sessions).selectinload(ExerciseSession.exercise),
            )
            .where(WorkoutSession.id == session_id)
        )
        orm = result.first()
        return _session_detail_to_rm(orm) if orm else None

    async def get_session_owner(self, session_id: int) -> int | None:
        result = await self._db.execute(select(WorkoutSession.user_id).where(WorkoutSession.id == session_id))
        row = result.first()
        return row.user_id if row else None

    # ---------- Personal records ----------

    async def list_user_personal_records(self, user_id: int) -> list[PersonalRecordReadModel]:
        result = await self._db.scalars(
            select(PersonalRecord)
            .options(selectinload(PersonalRecord.exercise))
            .where(PersonalRecord.user_id == user_id)
            .order_by(PersonalRecord.recorded_at.desc())
        )
        return [_pr_to_rm(pr) for pr in result.all()]
