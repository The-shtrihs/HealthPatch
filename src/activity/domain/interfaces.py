from abc import ABC, abstractmethod

from src.activity.domain.models import (
    ExerciseDomain,
    ExerciseSessionDomain,
    MuscleGroupDomain,
    PersonalRecordDomain,
    PlanTrainingDomain,
    PlanTrainingExerciseDomain,
    Weekday,
    WorkoutPlanDomain,
    WorkoutSessionDomain,
    WorkoutSetDomain,
)


class IActivityRepository(ABC):
    # Muscle groups
    @abstractmethod
    async def list_muscle_groups(self) -> list[MuscleGroupDomain]: ...

    @abstractmethod
    async def get_muscle_group_by_id(self, muscle_group_id: int) -> MuscleGroupDomain | None: ...

    @abstractmethod
    async def create_muscle_group(self, name: str) -> MuscleGroupDomain: ...

    # Exercises
    @abstractmethod
    async def get_exercise_by_id(self, exercise_id: int) -> ExerciseDomain | None: ...

    @abstractmethod
    async def list_exercises(self, search: str | None, offset: int, limit: int) -> tuple[list[ExerciseDomain], int]: ...

    @abstractmethod
    async def create_exercise(
        self,
        name: str,
        primary_muscle_group_id: int | None,
        secondary_muscle_group_ids: list[int],
    ) -> ExerciseDomain: ...

    # Workout plans
    @abstractmethod
    async def get_plan_by_id(self, plan_id: int) -> WorkoutPlanDomain | None: ...

    @abstractmethod
    async def get_plan_with_trainings(self, plan_id: int) -> WorkoutPlanDomain | None: ...

    @abstractmethod
    async def list_public_plans(self, offset: int, limit: int) -> tuple[list[WorkoutPlanDomain], int]: ...

    @abstractmethod
    async def list_user_plans(self, user_id: int, offset: int, limit: int) -> tuple[list[WorkoutPlanDomain], int]: ...

    @abstractmethod
    async def create_plan(self, author_id: int, title: str, description: str | None, is_public: bool) -> WorkoutPlanDomain: ...

    @abstractmethod
    async def save_plan(self, plan: WorkoutPlanDomain) -> WorkoutPlanDomain: ...

    @abstractmethod
    async def delete_plan(self, plan_id: int) -> None: ...

    # Plan trainings
    @abstractmethod
    async def get_training_by_id(self, training_id: int) -> PlanTrainingDomain | None: ...

    @abstractmethod
    async def get_training_with_exercises(self, training_id: int) -> PlanTrainingDomain | None: ...

    @abstractmethod
    async def add_training(self, plan_id: int, name: str, weekday: Weekday | None, order_num: int) -> PlanTrainingDomain: ...

    @abstractmethod
    async def delete_training(self, training_id: int) -> None: ...

    # Plan-training exercises
    @abstractmethod
    async def get_training_exercise_by_id(self, pte_id: int) -> PlanTrainingExerciseDomain | None: ...

    @abstractmethod
    async def add_exercise_to_training(
        self,
        plan_training_id: int,
        exercise_id: int,
        order_num: int,
        target_sets: int,
        target_reps: int,
        target_weight_pct: float | None,
    ) -> PlanTrainingExerciseDomain: ...

    @abstractmethod
    async def delete_training_exercise(self, pte_id: int) -> None: ...

    # Workout sessions
    @abstractmethod
    async def get_session_by_id(self, session_id: int) -> WorkoutSessionDomain | None: ...

    @abstractmethod
    async def get_session_with_exercises(self, session_id: int) -> WorkoutSessionDomain | None: ...

    @abstractmethod
    async def list_user_sessions(self, user_id: int, offset: int, limit: int) -> tuple[list[WorkoutSessionDomain], int]: ...

    @abstractmethod
    async def create_session(self, user_id: int, plan_training_id: int | None, started_at) -> WorkoutSessionDomain: ...

    @abstractmethod
    async def save_session(self, session: WorkoutSessionDomain) -> WorkoutSessionDomain: ...

    # Exercise sessions
    @abstractmethod
    async def get_exercise_session_by_id(self, exercise_session_id: int) -> ExerciseSessionDomain | None: ...

    @abstractmethod
    async def add_exercise_to_session(
        self,
        workout_session_id: int,
        exercise_id: int,
        order_num: int,
        is_from_template: bool,
    ) -> ExerciseSessionDomain: ...

    # Sets
    @abstractmethod
    async def add_set(
        self,
        exercise_session_id: int,
        set_number: int,
        reps: int,
        weight: float,
    ) -> WorkoutSetDomain: ...

    # Personal records
    @abstractmethod
    async def get_personal_record(self, user_id: int, exercise_id: int) -> PersonalRecordDomain | None: ...

    @abstractmethod
    async def get_personal_record_by_id(self, pr_id: int) -> PersonalRecordDomain | None: ...

    @abstractmethod
    async def list_user_personal_records(self, user_id: int) -> list[PersonalRecordDomain]: ...

    @abstractmethod
    async def upsert_personal_record(self, user_id: int, exercise_id: int, weight: float, recorded_at) -> PersonalRecordDomain: ...

    @abstractmethod
    async def delete_personal_record(self, pr_id: int) -> None: ...


class IActivityUnitOfWork(ABC):
    repo: IActivityRepository

    @abstractmethod
    async def __aenter__(self) -> "IActivityUnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
