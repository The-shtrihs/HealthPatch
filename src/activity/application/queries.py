from dataclasses import dataclass


@dataclass
class ListMuscleGroupsQuery:
    pass


@dataclass
class ListExercisesQuery:
    search: str | None
    page: int
    size: int


@dataclass
class GetExerciseQuery:
    exercise_id: int


@dataclass
class ListPublicPlansQuery:
    page: int
    size: int


@dataclass
class ListMyPlansQuery:
    user_id: int
    page: int
    size: int


@dataclass
class GetPlanDetailQuery:
    plan_id: int
    viewer_id: int


@dataclass
class ListUserSessionsQuery:
    user_id: int
    page: int
    size: int


@dataclass
class GetSessionDetailQuery:
    session_id: int
    user_id: int


@dataclass
class ListPersonalRecordsQuery:
    user_id: int
