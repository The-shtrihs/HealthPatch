from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.activity import (
    Exercise,
    ExerciseMuscleGroup,
    ExerciseSession,
    MuscleGroup,
    PersonalRecord,
    PlanTraining,
    PlanTrainingExercise,
    Weekday,
    WorkoutPlan,
    WorkoutSession,
    WorkoutSet,
)


class ActivityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_muscle_group(self, name: str) -> MuscleGroup:
        mg = MuscleGroup(name=name)
        self.db.add(mg)
        await self.db.flush()
        await self.db.refresh(mg)
        return mg

    async def get_muscle_group_by_id(self, muscle_group_id: int) -> MuscleGroup | None:
        return await self.db.get(MuscleGroup, muscle_group_id)

    async def list_muscle_groups(self) -> list[MuscleGroup]:
        result = await self.db.scalars(select(MuscleGroup).order_by(MuscleGroup.name))
        return list(result.all())

    async def create_exercise(self, name: str, primary_muscle_group_id: int | None, secondary_muscle_group_ids: list[int]) -> Exercise:
        exercise = Exercise(name=name, primary_muscle_group_id=primary_muscle_group_id)
        self.db.add(exercise)
        await self.db.flush()

        for mg_id in secondary_muscle_group_ids:
            link = ExerciseMuscleGroup(exercise_id=exercise.id, muscle_group_id=mg_id)
            self.db.add(link)

        await self.db.flush()
        await self.db.refresh(exercise)
        return exercise

    async def get_exercise_by_id(self, exercise_id: int) -> Exercise | None:
        result = await self.db.scalars(
            select(Exercise)
            .options(
                selectinload(Exercise.primary_muscle_group),
                selectinload(Exercise.secondary_muscle_group_links).selectinload(ExerciseMuscleGroup.muscle_group),
            )
            .where(Exercise.id == exercise_id)
        )
        return result.first()

    async def list_exercises(self, search: str | None, offset: int, limit: int) -> tuple[list[Exercise], int]:
        query = select(Exercise).options(
            selectinload(Exercise.primary_muscle_group),
            selectinload(Exercise.secondary_muscle_group_links).selectinload(ExerciseMuscleGroup.muscle_group),
        )
        count_query = select(func.count()).select_from(Exercise)

        if search:
            pattern = f"%{search}%"
            query = query.where(Exercise.name.ilike(pattern))
            count_query = count_query.where(Exercise.name.ilike(pattern))

        total = (await self.db.scalar(count_query)) or 0
        items = list((await self.db.scalars(query.offset(offset).limit(limit).order_by(Exercise.name))).all())
        return items, total

    async def create_plan(self, author_id: int, title: str, description: str | None, is_public: bool) -> WorkoutPlan:
        plan = WorkoutPlan(author_id=author_id, title=title, description=description, is_public=is_public)
        self.db.add(plan)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def get_plan_by_id(self, plan_id: int) -> WorkoutPlan | None:
        return await self.db.get(WorkoutPlan, plan_id)

    async def get_plan_with_trainings(self, plan_id: int) -> WorkoutPlan | None:
        result = await self.db.scalars(
            select(WorkoutPlan)
            .options(selectinload(WorkoutPlan.trainings).selectinload(PlanTraining.exercises).selectinload(PlanTrainingExercise.exercise))
            .where(WorkoutPlan.id == plan_id)
        )
        return result.first()

    async def list_public_plans(self, offset: int, limit: int) -> tuple[list[WorkoutPlan], int]:
        query = select(WorkoutPlan).where(WorkoutPlan.is_public.is_(True))
        total = (await self.db.scalar(select(func.count()).select_from(WorkoutPlan).where(WorkoutPlan.is_public.is_(True)))) or 0
        items = list((await self.db.scalars(query.offset(offset).limit(limit).order_by(WorkoutPlan.id.desc()))).all())
        return items, total

    async def list_user_plans(self, user_id: int, offset: int, limit: int) -> tuple[list[WorkoutPlan], int]:
        query = select(WorkoutPlan).where(WorkoutPlan.author_id == user_id)
        total = (await self.db.scalar(select(func.count()).select_from(WorkoutPlan).where(WorkoutPlan.author_id == user_id))) or 0
        items = list((await self.db.scalars(query.offset(offset).limit(limit).order_by(WorkoutPlan.id.desc()))).all())
        return items, total

    async def update_plan(self, plan: WorkoutPlan, **fields) -> WorkoutPlan:
        for key, value in fields.items():
            if value is not None:
                setattr(plan, key, value)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def delete_plan(self, plan: WorkoutPlan) -> None:
        await self.db.delete(plan)
        await self.db.flush()

    async def add_training(self, plan_id: int, name: str, weekday: Weekday | None, order_num: int) -> PlanTraining:
        training = PlanTraining(plan_id=plan_id, name=name, weekday=weekday, order_num=order_num)
        self.db.add(training)
        await self.db.flush()
        await self.db.refresh(training)
        return training

    async def get_training_by_id(self, training_id: int) -> PlanTraining | None:
        return await self.db.get(PlanTraining, training_id)

    async def get_training_with_exercises(self, training_id: int) -> PlanTraining | None:
        result = await self.db.scalars(
            select(PlanTraining)
            .options(selectinload(PlanTraining.exercises).selectinload(PlanTrainingExercise.exercise))
            .where(PlanTraining.id == training_id)
        )
        return result.first()

    async def delete_training(self, training: PlanTraining) -> None:
        await self.db.delete(training)
        await self.db.flush()

    async def add_exercise_to_training(
        self,
        plan_training_id: int,
        exercise_id: int,
        order_num: int,
        target_sets: int,
        target_reps: int,
        target_weight_pct: float | None,
    ) -> PlanTrainingExercise:
        pte = PlanTrainingExercise(
            plan_training_id=plan_training_id,
            exercise_id=exercise_id,
            order_num=order_num,
            target_sets=target_sets,
            target_reps=target_reps,
            target_weight_pct=target_weight_pct,
        )
        self.db.add(pte)
        await self.db.flush()
        await self.db.refresh(pte)
        return pte

    async def get_training_exercise_by_id(self, pte_id: int) -> PlanTrainingExercise | None:
        return await self.db.get(PlanTrainingExercise, pte_id)

    async def delete_training_exercise(self, pte: PlanTrainingExercise) -> None:
        await self.db.delete(pte)
        await self.db.flush()

    async def create_session(self, user_id: int, plan_training_id: int | None) -> WorkoutSession:
        session = WorkoutSession(
            user_id=user_id,
            plan_training_id=plan_training_id,
            started_at=datetime.now(UTC),
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session_by_id(self, session_id: int) -> WorkoutSession | None:
        return await self.db.get(WorkoutSession, session_id)

    async def get_session_with_exercises(self, session_id: int) -> WorkoutSession | None:
        result = await self.db.scalars(
            select(WorkoutSession)
            .options(
                selectinload(WorkoutSession.exercise_sessions).selectinload(ExerciseSession.sets),
                selectinload(WorkoutSession.exercise_sessions).selectinload(ExerciseSession.exercise),
            )
            .where(WorkoutSession.id == session_id)
        )
        return result.first()

    async def list_user_sessions(self, user_id: int, offset: int, limit: int) -> tuple[list[WorkoutSession], int]:
        query = select(WorkoutSession).where(WorkoutSession.user_id == user_id)
        total = (await self.db.scalar(select(func.count()).select_from(WorkoutSession).where(WorkoutSession.user_id == user_id))) or 0
        items = list((await self.db.scalars(query.offset(offset).limit(limit).order_by(WorkoutSession.started_at.desc()))).all())
        return items, total

    async def end_session(self, session: WorkoutSession) -> WorkoutSession:
        session.ended_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def add_exercise_to_session(self, workout_session_id: int, exercise_id: int, order_num: int, is_from_template: bool) -> ExerciseSession:
        es = ExerciseSession(
            workout_session_id=workout_session_id,
            exercise_id=exercise_id,
            order_num=order_num,
            is_from_template=is_from_template,
        )
        self.db.add(es)
        await self.db.flush()
        await self.db.refresh(es)
        return es

    async def get_exercise_session_by_id(self, exercise_session_id: int) -> ExerciseSession | None:
        return await self.db.get(ExerciseSession, exercise_session_id)

    async def add_set(self, exercise_session_id: int, set_number: int, reps: int, weight: float) -> WorkoutSet:
        ws = WorkoutSet(
            exercise_session_id=exercise_session_id,
            set_number=set_number,
            reps=reps,
            weight=weight,
        )
        self.db.add(ws)
        await self.db.flush()
        await self.db.refresh(ws)
        return ws

    async def get_personal_record(self, user_id: int, exercise_id: int) -> PersonalRecord | None:
        result = await self.db.scalars(select(PersonalRecord).where(PersonalRecord.user_id == user_id, PersonalRecord.exercise_id == exercise_id))
        return result.first()

    async def upsert_personal_record(self, user_id: int, exercise_id: int, weight: float) -> PersonalRecord:
        pr = await self.get_personal_record(user_id, exercise_id)
        if pr is None:
            pr = PersonalRecord(user_id=user_id, exercise_id=exercise_id, weight=weight, recorded_at=datetime.now(UTC))
            self.db.add(pr)
        else:
            pr.weight = weight
            pr.recorded_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(pr)
        return pr

    async def get_personal_record_by_id(self, pr_id: int) -> PersonalRecord | None:
        return await self.db.get(PersonalRecord, pr_id)

    async def delete_personal_record(self, pr: PersonalRecord) -> None:
        await self.db.delete(pr)
        await self.db.flush()

    async def list_user_personal_records(self, user_id: int) -> list[PersonalRecord]:
        result = await self.db.scalars(
            select(PersonalRecord)
            .options(selectinload(PersonalRecord.exercise))
            .where(PersonalRecord.user_id == user_id)
            .order_by(PersonalRecord.recorded_at.desc())
        )
        return list(result.all())
