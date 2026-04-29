from abc import ABC, abstractmethod

from src.activity.application.read_models import (
    ExerciseReadModel,
    MuscleGroupReadModel,
    PageReadModel,
    PersonalRecordReadModel,
    WorkoutPlanDetailReadModel,
    WorkoutPlanSummaryReadModel,
    WorkoutSessionDetailReadModel,
    WorkoutSessionSummaryReadModel,
)


class IActivityReadRepository(ABC):
    """Abstract interface for the read-side repository.
    Bypasses the domain layer; returns Read Models directly.
    """

    # ---------- Muscle groups ----------

    @abstractmethod
    async def list_muscle_groups(self) -> list[MuscleGroupReadModel]:
        pass

    # ---------- Exercises ----------

    @abstractmethod
    async def get_exercise(self, exercise_id: int) -> ExerciseReadModel | None:
        pass

    @abstractmethod
    async def list_exercises(
        self,
        search: str | None,
        offset: int,
        limit: int,
        page: int,
        size: int,
    ) -> PageReadModel[ExerciseReadModel]:
        pass

    # ---------- Workout plans ----------

    @abstractmethod
    async def list_public_plans(self, offset: int, limit: int, page: int, size: int) -> PageReadModel[WorkoutPlanSummaryReadModel]:
        pass

    @abstractmethod
    async def list_user_plans(
        self,
        user_id: int,
        offset: int,
        limit: int,
        page: int,
        size: int,
    ) -> PageReadModel[WorkoutPlanSummaryReadModel]:
        pass

    @abstractmethod
    async def get_plan_detail(self, plan_id: int) -> WorkoutPlanDetailReadModel | None:
        pass

    @abstractmethod
    async def get_plan_visibility(self, plan_id: int) -> tuple[int, bool] | None:
        """Returns (author_id, is_public) for visibility checks without loading the aggregate."""
        pass

    # ---------- Workout sessions ----------

    @abstractmethod
    async def list_user_sessions(
        self,
        user_id: int,
        offset: int,
        limit: int,
        page: int,
        size: int,
    ) -> PageReadModel[WorkoutSessionSummaryReadModel]:
        pass

    @abstractmethod
    async def get_session_detail(self, session_id: int) -> WorkoutSessionDetailReadModel | None:
        pass

    @abstractmethod
    async def get_session_owner(self, session_id: int) -> int | None:
        pass

    # ---------- Personal records ----------

    @abstractmethod
    async def list_user_personal_records(self, user_id: int) -> list[PersonalRecordReadModel]:
        pass
