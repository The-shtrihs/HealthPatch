from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.activity.domain.errors import (
    ExerciseSessionNotFoundError,
    PersonalRecordNotFoundError,
    PlanTrainingExerciseNotFoundError,
    PlanTrainingNotFoundError,
    WorkoutPlanNotFoundError,
    WorkoutSessionNotFoundError,
)
from src.activity.domain.interfaces import IActivityRepository
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
from src.activity.domain.models import (
    Weekday as DomainWeekday,
)
from src.activity.infrastructure.mapper import (
    apply_domain_to_workout_plan_orm,
    apply_domain_to_workout_session_orm,
    domain_weekday_to_orm,
    exercise_session_to_domain,
    exercise_to_domain,
    muscle_group_to_domain,
    personal_record_to_domain,
    plan_training_exercise_to_domain,
    plan_training_to_domain,
    workout_plan_to_domain,
    workout_session_to_domain,
    workout_set_to_domain,
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
    WorkoutSet,
)


class SqlAlchemyActivityRepository(IActivityRepository):
    def __init__(self, db: AsyncSession):
        self._db = db

    # ---------- Muscle groups ----------

    async def list_muscle_groups(self) -> list[MuscleGroupDomain]:
        result = await self._db.scalars(select(MuscleGroup).order_by(MuscleGroup.name))
        return [muscle_group_to_domain(mg) for mg in result.all()]

    async def get_muscle_group_by_id(self, muscle_group_id: int) -> MuscleGroupDomain | None:
        orm = await self._db.get(MuscleGroup, muscle_group_id)
        return muscle_group_to_domain(orm) if orm else None

    async def create_muscle_group(self, name: str) -> MuscleGroupDomain:
        orm = MuscleGroup(name=name)
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return muscle_group_to_domain(orm)

    # ---------- Exercises ----------

    async def _load_exercise_orm(self, exercise_id: int) -> Exercise | None:
        result = await self._db.scalars(
            select(Exercise)
            .options(
                selectinload(Exercise.primary_muscle_group),
                selectinload(Exercise.secondary_muscle_group_links).selectinload(ExerciseMuscleGroup.muscle_group),
            )
            .where(Exercise.id == exercise_id)
        )
        return result.first()

    async def get_exercise_by_id(self, exercise_id: int) -> ExerciseDomain | None:
        orm = await self._load_exercise_orm(exercise_id)
        return exercise_to_domain(orm) if orm else None

    async def list_exercises(self, search: str | None, offset: int, limit: int) -> tuple[list[ExerciseDomain], int]:
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
        return [exercise_to_domain(e) for e in items], total

    async def create_exercise(
        self,
        name: str,
        primary_muscle_group_id: int | None,
        secondary_muscle_group_ids: list[int],
    ) -> ExerciseDomain:
        orm = Exercise(name=name, primary_muscle_group_id=primary_muscle_group_id)
        self._db.add(orm)
        await self._db.flush()

        for mg_id in secondary_muscle_group_ids:
            self._db.add(ExerciseMuscleGroup(exercise_id=orm.id, muscle_group_id=mg_id))

        await self._db.flush()
        full = await self._load_exercise_orm(orm.id)
        return exercise_to_domain(full)

    # ---------- Workout plans ----------

    async def get_plan_by_id(self, plan_id: int) -> WorkoutPlanDomain | None:
        orm = await self._db.get(WorkoutPlan, plan_id)
        return workout_plan_to_domain(orm) if orm else None

    async def _load_plan_with_trainings_orm(self, plan_id: int) -> WorkoutPlan | None:
        result = await self._db.scalars(
            select(WorkoutPlan)
            .options(selectinload(WorkoutPlan.trainings).selectinload(PlanTraining.exercises).selectinload(PlanTrainingExercise.exercise))
            .where(WorkoutPlan.id == plan_id)
        )
        return result.first()

    async def get_plan_with_trainings(self, plan_id: int) -> WorkoutPlanDomain | None:
        orm = await self._load_plan_with_trainings_orm(plan_id)
        return workout_plan_to_domain(orm, include_trainings=True) if orm else None

    async def list_public_plans(self, offset: int, limit: int) -> tuple[list[WorkoutPlanDomain], int]:
        query = select(WorkoutPlan).where(WorkoutPlan.is_public.is_(True))
        total = (await self._db.scalar(select(func.count()).select_from(WorkoutPlan).where(WorkoutPlan.is_public.is_(True)))) or 0
        items = list((await self._db.scalars(query.offset(offset).limit(limit).order_by(WorkoutPlan.id.desc()))).all())
        return [workout_plan_to_domain(p) for p in items], total

    async def list_user_plans(self, user_id: int, offset: int, limit: int) -> tuple[list[WorkoutPlanDomain], int]:
        query = select(WorkoutPlan).where(WorkoutPlan.author_id == user_id)
        total = (await self._db.scalar(select(func.count()).select_from(WorkoutPlan).where(WorkoutPlan.author_id == user_id))) or 0
        items = list((await self._db.scalars(query.offset(offset).limit(limit).order_by(WorkoutPlan.id.desc()))).all())
        return [workout_plan_to_domain(p) for p in items], total

    async def create_plan(self, author_id: int, title: str, description: str | None, is_public: bool) -> WorkoutPlanDomain:
        orm = WorkoutPlan(author_id=author_id, title=title, description=description, is_public=is_public)
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return workout_plan_to_domain(orm)

    async def save_plan(self, plan: WorkoutPlanDomain) -> WorkoutPlanDomain:
        if plan.id is None:
            raise WorkoutPlanNotFoundError()
        orm = await self._db.get(WorkoutPlan, plan.id)
        if orm is None:
            raise WorkoutPlanNotFoundError(plan.id)
        apply_domain_to_workout_plan_orm(plan, orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return workout_plan_to_domain(orm)

    async def delete_plan(self, plan_id: int) -> None:
        orm = await self._db.get(WorkoutPlan, plan_id)
        if orm is None:
            raise WorkoutPlanNotFoundError(plan_id)
        await self._db.delete(orm)
        await self._db.flush()

    # ---------- Plan trainings ----------

    async def get_training_by_id(self, training_id: int) -> PlanTrainingDomain | None:
        orm = await self._db.get(PlanTraining, training_id)
        return plan_training_to_domain(orm, include_exercises=False) if orm else None

    async def get_training_with_exercises(self, training_id: int) -> PlanTrainingDomain | None:
        result = await self._db.scalars(
            select(PlanTraining)
            .options(selectinload(PlanTraining.exercises).selectinload(PlanTrainingExercise.exercise))
            .where(PlanTraining.id == training_id)
        )
        orm = result.first()
        return plan_training_to_domain(orm) if orm else None

    async def add_training(self, plan_id: int, name: str, weekday: DomainWeekday | None, order_num: int) -> PlanTrainingDomain:
        orm = PlanTraining(
            plan_id=plan_id,
            name=name,
            weekday=domain_weekday_to_orm(weekday),
            order_num=order_num,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return plan_training_to_domain(orm, include_exercises=False)

    async def delete_training(self, training_id: int) -> None:
        orm = await self._db.get(PlanTraining, training_id)
        if orm is None:
            raise PlanTrainingNotFoundError(training_id)
        await self._db.delete(orm)
        await self._db.flush()

    # ---------- Plan-training exercises ----------

    async def get_training_exercise_by_id(self, pte_id: int) -> PlanTrainingExerciseDomain | None:
        result = await self._db.scalars(
            select(PlanTrainingExercise).options(selectinload(PlanTrainingExercise.exercise)).where(PlanTrainingExercise.id == pte_id)
        )
        orm = result.first()
        return plan_training_exercise_to_domain(orm) if orm else None

    async def add_exercise_to_training(
        self,
        plan_training_id: int,
        exercise_id: int,
        order_num: int,
        target_sets: int,
        target_reps: int,
        target_weight_pct: float | None,
    ) -> PlanTrainingExerciseDomain:
        orm = PlanTrainingExercise(
            plan_training_id=plan_training_id,
            exercise_id=exercise_id,
            order_num=order_num,
            target_sets=target_sets,
            target_reps=target_reps,
            target_weight_pct=target_weight_pct,
        )
        self._db.add(orm)
        await self._db.flush()
        result = await self._db.scalars(
            select(PlanTrainingExercise).options(selectinload(PlanTrainingExercise.exercise)).where(PlanTrainingExercise.id == orm.id)
        )
        full = result.first()
        return plan_training_exercise_to_domain(full)

    async def delete_training_exercise(self, pte_id: int) -> None:
        orm = await self._db.get(PlanTrainingExercise, pte_id)
        if orm is None:
            raise PlanTrainingExerciseNotFoundError(pte_id)
        await self._db.delete(orm)
        await self._db.flush()

    # ---------- Workout sessions ----------

    async def get_session_by_id(self, session_id: int) -> WorkoutSessionDomain | None:
        orm = await self._db.get(WorkoutSession, session_id)
        return workout_session_to_domain(orm) if orm else None

    async def get_session_with_exercises(self, session_id: int) -> WorkoutSessionDomain | None:
        result = await self._db.scalars(
            select(WorkoutSession)
            .options(
                selectinload(WorkoutSession.exercise_sessions).selectinload(ExerciseSession.sets),
                selectinload(WorkoutSession.exercise_sessions).selectinload(ExerciseSession.exercise),
            )
            .where(WorkoutSession.id == session_id)
        )
        orm = result.first()
        return workout_session_to_domain(orm, include_children=True) if orm else None

    async def list_user_sessions(self, user_id: int, offset: int, limit: int) -> tuple[list[WorkoutSessionDomain], int]:
        query = select(WorkoutSession).where(WorkoutSession.user_id == user_id)
        total = (await self._db.scalar(select(func.count()).select_from(WorkoutSession).where(WorkoutSession.user_id == user_id))) or 0
        items = list((await self._db.scalars(query.offset(offset).limit(limit).order_by(WorkoutSession.started_at.desc()))).all())
        return [workout_session_to_domain(s) for s in items], total

    async def create_session(self, user_id: int, plan_training_id: int | None, started_at: datetime) -> WorkoutSessionDomain:
        orm = WorkoutSession(
            user_id=user_id,
            plan_training_id=plan_training_id,
            started_at=started_at,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return workout_session_to_domain(orm)

    async def save_session(self, session: WorkoutSessionDomain) -> WorkoutSessionDomain:
        if session.id is None:
            raise WorkoutSessionNotFoundError()
        orm = await self._db.get(WorkoutSession, session.id)
        if orm is None:
            raise WorkoutSessionNotFoundError(session.id)
        apply_domain_to_workout_session_orm(session, orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return workout_session_to_domain(orm)

    # ---------- Exercise sessions ----------

    async def get_exercise_session_by_id(self, exercise_session_id: int) -> ExerciseSessionDomain | None:
        orm = await self._db.get(ExerciseSession, exercise_session_id)
        return exercise_session_to_domain(orm, include_sets=False) if orm else None

    async def add_exercise_to_session(
        self,
        workout_session_id: int,
        exercise_id: int,
        order_num: int,
        is_from_template: bool,
    ) -> ExerciseSessionDomain:
        orm = ExerciseSession(
            workout_session_id=workout_session_id,
            exercise_id=exercise_id,
            order_num=order_num,
            is_from_template=is_from_template,
        )
        self._db.add(orm)
        await self._db.flush()
        result = await self._db.scalars(select(ExerciseSession).options(selectinload(ExerciseSession.exercise)).where(ExerciseSession.id == orm.id))
        full = result.first()
        return exercise_session_to_domain(full, include_sets=False)

    # ---------- Sets ----------

    async def add_set(
        self,
        exercise_session_id: int,
        set_number: int,
        reps: int,
        weight: float,
    ) -> WorkoutSetDomain:
        es_exists = await self._db.get(ExerciseSession, exercise_session_id)
        if es_exists is None:
            raise ExerciseSessionNotFoundError(exercise_session_id)
        orm = WorkoutSet(
            exercise_session_id=exercise_session_id,
            set_number=set_number,
            reps=reps,
            weight=weight,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return workout_set_to_domain(orm)

    # ---------- Personal records ----------

    async def get_personal_record(self, user_id: int, exercise_id: int) -> PersonalRecordDomain | None:
        result = await self._db.scalars(
            select(PersonalRecord)
            .options(selectinload(PersonalRecord.exercise))
            .where(
                PersonalRecord.user_id == user_id,
                PersonalRecord.exercise_id == exercise_id,
            )
        )
        orm = result.first()
        return personal_record_to_domain(orm) if orm else None

    async def get_personal_record_by_id(self, pr_id: int) -> PersonalRecordDomain | None:
        result = await self._db.scalars(select(PersonalRecord).options(selectinload(PersonalRecord.exercise)).where(PersonalRecord.id == pr_id))
        orm = result.first()
        return personal_record_to_domain(orm) if orm else None

    async def list_user_personal_records(self, user_id: int) -> list[PersonalRecordDomain]:
        result = await self._db.scalars(
            select(PersonalRecord)
            .options(selectinload(PersonalRecord.exercise))
            .where(PersonalRecord.user_id == user_id)
            .order_by(PersonalRecord.recorded_at.desc())
        )
        return [personal_record_to_domain(pr) for pr in result.all()]

    async def upsert_personal_record(
        self,
        user_id: int,
        exercise_id: int,
        weight: float,
        recorded_at: datetime,
    ) -> PersonalRecordDomain:
        result = await self._db.scalars(
            select(PersonalRecord).where(
                PersonalRecord.user_id == user_id,
                PersonalRecord.exercise_id == exercise_id,
            )
        )
        orm = result.first()
        if orm is None:
            orm = PersonalRecord(
                user_id=user_id,
                exercise_id=exercise_id,
                weight=weight,
                recorded_at=recorded_at,
            )
            self._db.add(orm)
        else:
            orm.weight = weight
            orm.recorded_at = recorded_at
        await self._db.flush()

        # reload with exercise relationship
        reloaded = await self._db.scalars(select(PersonalRecord).options(selectinload(PersonalRecord.exercise)).where(PersonalRecord.id == orm.id))
        full = reloaded.first()
        return personal_record_to_domain(full)

    async def delete_personal_record(self, pr_id: int) -> None:
        orm = await self._db.get(PersonalRecord, pr_id)
        if orm is None:
            raise PersonalRecordNotFoundError(pr_id)
        await self._db.delete(orm)
        await self._db.flush()
