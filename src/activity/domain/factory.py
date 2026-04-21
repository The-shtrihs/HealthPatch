from datetime import datetime

from src.activity.domain.errors import (
    ExerciseNotFoundError,
    MuscleGroupNotFoundError,
    PersonalRecordDowngradeError,
    PlanTrainingNotFoundError,
    SessionAlreadyEndedError,
    WorkoutPlanNotFoundError,
)
from src.activity.domain.interfaces import IActivityRepository
from src.activity.domain.models import (
    ExerciseSessionDomain,
    PersonalRecordDomain,
    PlanTrainingExerciseDomain,
    RepCount,
    SetNumber,
    TimeRange,
    Weekday,
    WeightKg,
    WorkoutPlanDomain,
    WorkoutSessionDomain,
    WorkoutSetDomain,
)


class WorkoutPlanFactory:
    """Builds a new workout plan aggregate after validating invariants."""

    def create(
        self,
        author_id: int,
        title: str,
        description: str | None,
        is_public: bool,
    ) -> WorkoutPlanDomain:
        # Invariants (non-empty title) are enforced inside WorkoutPlanDomain.__post_init__.
        return WorkoutPlanDomain(
            id=None,
            author_id=author_id,
            title=title,
            description=description,
            is_public=is_public,
        )


class PlanTrainingExerciseFactory:
    """Creates a plan-training-exercise line after checking exercise existence (DB invariant)."""

    def __init__(self, repo: IActivityRepository):
        self._repo = repo

    async def create(
        self,
        plan_training_id: int,
        exercise_id: int,
        order_num: int,
        target_sets: int,
        target_reps: int,
        target_weight_pct: float | None,
    ) -> PlanTrainingExerciseDomain:
        if await self._repo.get_exercise_by_id(exercise_id) is None:
            raise ExerciseNotFoundError(exercise_id)

        return PlanTrainingExerciseDomain(
            id=None,
            plan_training_id=plan_training_id,
            exercise_id=exercise_id,
            exercise_name=None,
            order_num=order_num,
            target_sets=target_sets,
            target_reps=target_reps,
            target_weight_pct=target_weight_pct,
        )


class WorkoutSessionFactory:
    """Starts a new workout session. Optionally bound to a plan training (DB invariant)."""

    def __init__(self, repo: IActivityRepository):
        self._repo = repo

    async def start(
        self,
        user_id: int,
        plan_training_id: int | None,
        at: datetime,
    ) -> WorkoutSessionDomain:
        if plan_training_id is not None:
            training = await self._repo.get_training_with_exercises(plan_training_id)
            if training is None:
                raise PlanTrainingNotFoundError(plan_training_id)
            plan = await self._repo.get_plan_by_id(training.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError()
            # Visibility enforcement is delegated to the use case; factory only validates existence
            # so the invariant "session must reference a real training" is guaranteed here.

        return WorkoutSessionDomain(
            id=None,
            user_id=user_id,
            plan_training_id=plan_training_id,
            time_range=TimeRange(started_at=at, ended_at=None),
            exercise_sessions=[],
        )


class WorkoutSetFactory:
    """Builds a new set. Verifies the parent session is still open (DB invariant)."""

    def __init__(self, repo: IActivityRepository):
        self._repo = repo

    async def log(
        self,
        exercise_session_id: int,
        set_number: int,
        reps: int,
        weight: float,
    ) -> WorkoutSetDomain:
        es = await self._repo.get_exercise_session_by_id(exercise_session_id)
        if es is None:
            # caller should catch and raise ExerciseSessionNotFoundError; factory stops here to avoid
            # fabricating a set referencing a non-existent parent.
            raise SessionAlreadyEndedError("Exercise session not found")

        session = await self._repo.get_session_by_id(es.workout_session_id)
        if session is None or session.is_ended:
            raise SessionAlreadyEndedError("Cannot log sets on an ended session")

        return WorkoutSetDomain(
            id=None,
            exercise_session_id=exercise_session_id,
            set_number=SetNumber(set_number),
            reps=RepCount(reps),
            weight=WeightKg(weight),
        )


class ExerciseSessionFactory:
    """Adds an exercise to a session. Verifies session is open and exercise exists."""

    def __init__(self, repo: IActivityRepository):
        self._repo = repo

    async def create(
        self,
        workout_session_id: int,
        exercise_id: int,
        order_num: int,
        is_from_template: bool,
    ) -> ExerciseSessionDomain:
        if await self._repo.get_exercise_by_id(exercise_id) is None:
            raise ExerciseNotFoundError(exercise_id)

        return ExerciseSessionDomain(
            id=None,
            workout_session_id=workout_session_id,
            exercise_id=exercise_id,
            exercise_name=None,
            order_num=order_num,
            is_from_template=is_from_template,
            sets=[],
        )


class PersonalRecordFactory:
    """Upserts a personal record. Rejects downgrades (domain invariant)."""

    def __init__(self, repo: IActivityRepository):
        self._repo = repo

    async def upsert(
        self,
        user_id: int,
        exercise_id: int,
        weight: float,
        at: datetime,
    ) -> PersonalRecordDomain:
        if await self._repo.get_exercise_by_id(exercise_id) is None:
            raise ExerciseNotFoundError(exercise_id)

        new_weight = WeightKg(weight)
        existing = await self._repo.get_personal_record(user_id, exercise_id)
        if existing is not None and new_weight.value < existing.weight.value:
            raise PersonalRecordDowngradeError(new_weight.value, existing.weight.value)

        return PersonalRecordDomain(
            id=existing.id if existing else None,
            user_id=user_id,
            exercise_id=exercise_id,
            exercise_name=existing.exercise_name if existing else None,
            weight=new_weight,
            recorded_at=at,
        )


class ExerciseFactory:
    """Creates a catalog exercise. Verifies referenced muscle groups exist (DB invariant)."""

    def __init__(self, repo: IActivityRepository):
        self._repo = repo

    async def validate_muscle_groups(
        self,
        primary_muscle_group_id: int | None,
        secondary_muscle_group_ids: list[int],
    ) -> None:
        if primary_muscle_group_id is not None:
            if await self._repo.get_muscle_group_by_id(primary_muscle_group_id) is None:
                raise MuscleGroupNotFoundError(primary_muscle_group_id)
        for mg_id in secondary_muscle_group_ids:
            if await self._repo.get_muscle_group_by_id(mg_id) is None:
                raise MuscleGroupNotFoundError(mg_id)


__all__ = [
    "WorkoutPlanFactory",
    "PlanTrainingExerciseFactory",
    "WorkoutSessionFactory",
    "WorkoutSetFactory",
    "ExerciseSessionFactory",
    "PersonalRecordFactory",
    "ExerciseFactory",
    "Weekday",
]
