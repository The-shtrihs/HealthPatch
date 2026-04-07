from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, NotResourceOwnerError, SessionAlreadyEndedError
from src.models.activity import Weekday
from src.repositories.activity import ActivityRepository
from src.schemas.activity import (
    AddExerciseToSessionRequest,
    AddExerciseToTrainingRequest,
    CreateExerciseRequest,
    CreateMuscleGroupRequest,
    CreatePlanTrainingRequest,
    CreateWorkoutPlanRequest,
    LogSetRequest,
    StartSessionRequest,
    UpdateWorkoutPlanRequest,
    UpsertPersonalRecordRequest,
)
from src.services.activity import ActivityService

pytestmark = pytest.mark.asyncio


class AsyncContextManagerMock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock(spec=ActivityRepository)


@pytest.fixture
def service(repo: AsyncMock) -> ActivityService:
    # Keep setup close to project guidance while still wiring the actual uow used by ActivityService.
    activity_service = ActivityService.__new__(ActivityService)
    activity_service.db = AsyncMock()
    activity_service.db.begin = MagicMock(return_value=AsyncContextManagerMock())

    uow = AsyncMock()
    uow.repo = repo
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False
    activity_service.uow = uow
    return activity_service


def _muscle_group(group_id: int, name: str) -> SimpleNamespace:
    return SimpleNamespace(id=group_id, name=name)


def _exercise(exercise_id: int, name: str, primary: SimpleNamespace | None = None, secondary: list[SimpleNamespace] | None = None) -> SimpleNamespace:
    secondary_links = [SimpleNamespace(muscle_group=mg, muscle_group_id=mg.id) for mg in (secondary or [])]
    return SimpleNamespace(
        id=exercise_id,
        name=name,
        primary_muscle_group=primary,
        secondary_muscle_group_links=secondary_links,
    )


def _plan_training_exercise(
    pte_id: int,
    exercise_id: int,
    exercise_name: str,
    order_num: int = 1,
    target_sets: int = 3,
    target_reps: int = 10,
    target_weight_pct: float | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=pte_id,
        exercise_id=exercise_id,
        order_num=order_num,
        target_sets=target_sets,
        target_reps=target_reps,
        target_weight_pct=target_weight_pct,
        exercise=SimpleNamespace(name=exercise_name),
    )


def _training(
    training_id: int,
    plan_id: int,
    name: str,
    order_num: int = 1,
    weekday: Weekday | None = None,
    exercises: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=training_id,
        plan_id=plan_id,
        name=name,
        order_num=order_num,
        weekday=weekday,
        exercises=exercises or [],
    )


def _plan(
    plan_id: int,
    author_id: int,
    title: str,
    is_public: bool,
    description: str | None = None,
    trainings: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=plan_id,
        author_id=author_id,
        title=title,
        description=description,
        is_public=is_public,
        trainings=trainings or [],
    )


def _workout_set(set_id: int, set_number: int, reps: int, weight: float) -> SimpleNamespace:
    return SimpleNamespace(id=set_id, set_number=set_number, reps=reps, weight=weight)


def _exercise_session(
    exercise_session_id: int,
    workout_session_id: int,
    exercise_id: int,
    order_num: int,
    is_from_template: bool,
    sets: list[SimpleNamespace] | None = None,
    exercise_name: str = "Exercise",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=exercise_session_id,
        workout_session_id=workout_session_id,
        exercise_id=exercise_id,
        order_num=order_num,
        is_from_template=is_from_template,
        sets=sets or [],
        exercise=SimpleNamespace(name=exercise_name),
    )


def _session(
    session_id: int,
    user_id: int,
    plan_training_id: int | None,
    ended_at: datetime | None = None,
    exercise_sessions: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=session_id,
        user_id=user_id,
        plan_training_id=plan_training_id,
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        ended_at=ended_at,
        exercise_sessions=exercise_sessions or [],
    )


def _personal_record(
    pr_id: int,
    user_id: int,
    exercise_id: int,
    exercise_name: str,
    weight: float,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=pr_id,
        user_id=user_id,
        exercise_id=exercise_id,
        exercise=SimpleNamespace(name=exercise_name),
        weight=weight,
        recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


async def test_list_muscle_groups_returns_response_list(repo: AsyncMock, service: ActivityService):
    repo.list_muscle_groups.return_value = [_muscle_group(1, "Back"), _muscle_group(2, "Chest")]

    result = await service.list_muscle_groups()

    assert len(result) == 2
    assert result[0].name == "Back"
    assert result[1].id == 2


async def test_create_muscle_group_returns_created_group(repo: AsyncMock, service: ActivityService):
    repo.create_muscle_group.return_value = _muscle_group(5, "Shoulders")

    result = await service.create_muscle_group(CreateMuscleGroupRequest(name="  Shoulders "))

    repo.create_muscle_group.assert_awaited_once_with("Shoulders")
    assert result.id == 5
    assert result.name == "Shoulders"


async def test_list_exercises_returns_paginated_response(repo: AsyncMock, service: ActivityService):
    chest = _muscle_group(1, "Chest")
    repo.list_exercises.return_value = ([_exercise(11, "Bench Press", primary=chest)], 1)

    result = await service.list_exercises(search="bench", page=2, size=5)

    repo.list_exercises.assert_awaited_once_with(search="bench", offset=5, limit=5)
    assert result.total == 1
    assert result.page == 2
    assert result.size == 5
    assert result.items[0].name == "Bench Press"


async def test_get_exercise_returns_exercise_response_when_found(repo: AsyncMock, service: ActivityService):
    chest = _muscle_group(1, "Chest")
    repo.get_exercise_by_id.return_value = _exercise(22, "Incline Press", primary=chest)

    result = await service.get_exercise(22)

    assert result.id == 22
    assert result.name == "Incline Press"
    assert result.primary_muscle_group is not None
    assert result.primary_muscle_group.name == "Chest"


async def test_get_exercise_with_missing_id_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_exercise_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await service.get_exercise(999)

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "Exercise with id 999 not found"


async def test_create_exercise_validates_muscles_and_returns_full_response(repo: AsyncMock, service: ActivityService):
    chest = _muscle_group(1, "Chest")
    triceps = _muscle_group(2, "Triceps")
    created = _exercise(44, "Bench Press", primary=chest, secondary=[triceps])
    repo.get_muscle_group_by_id.side_effect = [chest, triceps]
    repo.create_exercise.return_value = created
    repo.get_exercise_by_id.return_value = created

    payload = CreateExerciseRequest(name="  Bench Press ", primary_muscle_group_id=1, secondary_muscle_group_ids=[2])
    result = await service.create_exercise(payload)

    repo.create_exercise.assert_awaited_once_with("Bench Press", 1, [2])
    assert result.id == 44
    assert result.secondary_muscle_groups[0].name == "Triceps"


async def test_create_exercise_with_missing_primary_group_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_muscle_group_by_id.return_value = None
    payload = CreateExerciseRequest(name="Press", primary_muscle_group_id=17, secondary_muscle_group_ids=[])

    with pytest.raises(NotFoundError) as exc_info:
        await service.create_exercise(payload)

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "MuscleGroup with id 17 not found"


async def test_list_public_plans_returns_response(repo: AsyncMock, service: ActivityService):
    repo.list_public_plans.return_value = ([_plan(1, 7, "Public", True)], 1)

    result = await service.list_public_plans(page=1, size=20)

    assert result.total == 1
    assert result.items[0].title == "Public"


async def test_list_user_plans_returns_only_user_entries(repo: AsyncMock, service: ActivityService):
    repo.list_user_plans.return_value = ([_plan(2, 9, "Mine", False)], 1)

    result = await service.list_user_plans(user_id=9, page=1, size=10)

    repo.list_user_plans.assert_awaited_once_with(user_id=9, offset=0, limit=10)
    assert result.items[0].author_id == 9


async def test_get_plan_returns_plan_detail_for_authorized_user(repo: AsyncMock, service: ActivityService):
    pte = _plan_training_exercise(1, 101, "Bench Press")
    training = _training(11, plan_id=5, name="Push", order_num=1, weekday=Weekday.MON, exercises=[pte])
    repo.get_plan_with_trainings.return_value = _plan(5, author_id=7, title="Push Plan", is_public=False, trainings=[training])

    result = await service.get_plan(plan_id=5, requesting_user_id=7)

    assert result.id == 5
    assert result.trainings[0].name == "Push"
    assert result.trainings[0].exercises[0].exercise_name == "Bench Press"


async def test_get_plan_with_missing_plan_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_plan_with_trainings.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await service.get_plan(plan_id=999, requesting_user_id=1)

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "WorkoutPlan with id 999 not found"


async def test_get_plan_for_private_plan_by_non_owner_raises_forbidden(repo: AsyncMock, service: ActivityService):
    repo.get_plan_with_trainings.return_value = _plan(3, author_id=10, title="Private", is_public=False)

    with pytest.raises(ForbiddenError) as exc_info:
        await service.get_plan(plan_id=3, requesting_user_id=11)

    assert exc_info.value.error_code == "FORBIDDEN"
    assert exc_info.value.message == "This workout plan is private"


async def test_create_plan_returns_detail_with_trainings_and_exercises(repo: AsyncMock, service: ActivityService):
    created_plan = _plan(8, author_id=1, title="Plan", is_public=True)
    pte = _plan_training_exercise(5, exercise_id=100, exercise_name="Squat", order_num=1)
    full_training = _training(20, plan_id=8, name="Leg Day", order_num=1, weekday=Weekday.THU, exercises=[pte])
    full_plan = _plan(8, author_id=1, title="Plan", is_public=True, trainings=[full_training])

    repo.create_plan.return_value = created_plan
    repo.get_exercise_by_id.return_value = _exercise(100, "Squat")
    repo.add_training.return_value = _training(20, plan_id=8, name="Leg Day", order_num=1)
    repo.get_plan_with_trainings.return_value = full_plan

    payload = CreateWorkoutPlanRequest(
        title="Plan",
        description="Desc",
        is_public=True,
        trainings=[
            {
                "name": "Leg Day",
                "order_num": 1,
                "weekday": "thu",
                "exercises": [
                    {
                        "exercise_id": 100,
                        "order_num": 1,
                        "target_sets": 4,
                        "target_reps": 8,
                        "target_weight_pct": 80,
                    }
                ],
            }
        ],
    )

    result = await service.create_plan(user_id=1, payload=payload)

    assert result.id == 8
    assert result.trainings[0].name == "Leg Day"
    assert result.trainings[0].exercises[0].exercise_name == "Squat"


async def test_create_plan_with_missing_exercise_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.create_plan.return_value = _plan(8, author_id=1, title="Plan", is_public=False)
    repo.get_exercise_by_id.return_value = None

    payload = CreateWorkoutPlanRequest(
        title="Plan",
        description=None,
        is_public=False,
        trainings=[
            {
                "name": "Day",
                "order_num": 1,
                "weekday": "mon",
                "exercises": [
                    {
                        "exercise_id": 999,
                        "order_num": 1,
                        "target_sets": 3,
                        "target_reps": 10,
                        "target_weight_pct": None,
                    }
                ],
            }
        ],
    )

    with pytest.raises(NotFoundError) as exc_info:
        await service.create_plan(user_id=1, payload=payload)

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "Exercise with id 999 not found"


@pytest.mark.parametrize(
    ("plan", "error"),
    [
        (None, NotFoundError),
        (_plan(10, author_id=2, title="Other", is_public=False), ForbiddenError),
    ],
)
async def test_update_plan_with_missing_or_non_owned_plan_raises(
    repo: AsyncMock,
    service: ActivityService,
    plan: SimpleNamespace | None,
    error: type[Exception],
):
    repo.get_plan_by_id.return_value = plan

    with pytest.raises(error):
        await service.update_plan(plan_id=10, user_id=1, payload=UpdateWorkoutPlanRequest(title="Updated"))


async def test_update_plan_happy_path_returns_updated_response(repo: AsyncMock, service: ActivityService):
    existing = _plan(11, author_id=1, title="Old", is_public=False)
    updated = _plan(11, author_id=1, title="New", is_public=True)
    repo.get_plan_by_id.return_value = existing
    repo.update_plan.return_value = updated

    result = await service.update_plan(plan_id=11, user_id=1, payload=UpdateWorkoutPlanRequest(title="New", is_public=True))

    assert result.id == 11
    assert result.title == "New"
    assert result.is_public is True


@pytest.mark.parametrize(
    ("plan", "error"),
    [
        (None, NotFoundError),
        (_plan(3, author_id=9, title="Other", is_public=False), ForbiddenError),
    ],
)
async def test_delete_plan_with_missing_or_non_owned_plan_raises(
    repo: AsyncMock,
    service: ActivityService,
    plan: SimpleNamespace | None,
    error: type[Exception],
):
    repo.get_plan_by_id.return_value = plan

    with pytest.raises(error):
        await service.delete_plan(plan_id=3, user_id=1)


async def test_delete_plan_happy_path_calls_repository(repo: AsyncMock, service: ActivityService):
    owned_plan = _plan(4, author_id=1, title="Mine", is_public=False)
    repo.get_plan_by_id.return_value = owned_plan

    await service.delete_plan(plan_id=4, user_id=1)

    repo.delete_plan.assert_awaited_once_with(owned_plan)


async def test_add_training_happy_path_returns_training_response(repo: AsyncMock, service: ActivityService):
    repo.get_plan_by_id.return_value = _plan(20, author_id=1, title="P", is_public=False)
    created = _training(40, plan_id=20, name="Day 1", order_num=1, weekday=Weekday.MON)
    full = _training(40, plan_id=20, name="Day 1", order_num=1, weekday=Weekday.MON, exercises=[])
    repo.add_training.return_value = created
    repo.get_training_with_exercises.return_value = full

    result = await service.add_training(plan_id=20, user_id=1, payload=CreatePlanTrainingRequest(name="Day 1", weekday="mon", order_num=1))

    assert result.id == 40
    assert result.name == "Day 1"
    assert result.weekday == "mon"


async def test_add_training_with_missing_plan_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_plan_by_id.return_value = None

    with pytest.raises(NotFoundError):
        await service.add_training(plan_id=55, user_id=1, payload=CreatePlanTrainingRequest(name="Day", weekday=None, order_num=0))


async def test_add_training_with_other_owner_plan_raises_forbidden(repo: AsyncMock, service: ActivityService):
    repo.get_plan_by_id.return_value = _plan(20, author_id=99, title="Other", is_public=False)

    with pytest.raises(ForbiddenError):
        await service.add_training(plan_id=20, user_id=1, payload=CreatePlanTrainingRequest(name="Day", weekday=None, order_num=0))


async def test_delete_training_happy_path_calls_repository_delete(repo: AsyncMock, service: ActivityService):
    repo.get_plan_by_id.return_value = _plan(10, author_id=1, title="Mine", is_public=False)
    training = _training(8, plan_id=10, name="Day", order_num=1)
    repo.get_training_by_id.return_value = training

    await service.delete_training(plan_id=10, training_id=8, user_id=1)

    repo.delete_training.assert_awaited_once_with(training)


async def test_delete_training_with_missing_training_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_plan_by_id.return_value = _plan(10, author_id=1, title="Mine", is_public=False)
    repo.get_training_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await service.delete_training(plan_id=10, training_id=99, user_id=1)

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "PlanTraining with id 99 not found"


async def test_add_exercise_to_training_happy_path_returns_schema(repo: AsyncMock, service: ActivityService):
    repo.get_plan_by_id.return_value = _plan(1, author_id=1, title="Plan", is_public=False)
    repo.get_training_by_id.return_value = _training(2, plan_id=1, name="Day", order_num=1)
    repo.get_exercise_by_id.return_value = _exercise(4, "Deadlift")
    pte = _plan_training_exercise(6, exercise_id=4, exercise_name="Deadlift", order_num=1, target_sets=5, target_reps=5)
    repo.add_exercise_to_training.return_value = pte

    payload = AddExerciseToTrainingRequest(exercise_id=4, order_num=1, target_sets=5, target_reps=5, target_weight_pct=None)
    result = await service.add_exercise_to_training(plan_id=1, training_id=2, user_id=1, payload=payload)

    assert result.id == 6
    assert result.exercise_name == "Deadlift"


async def test_add_exercise_to_training_with_missing_exercise_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_plan_by_id.return_value = _plan(1, author_id=1, title="Plan", is_public=False)
    repo.get_training_by_id.return_value = _training(2, plan_id=1, name="Day", order_num=1)
    repo.get_exercise_by_id.return_value = None

    payload = AddExerciseToTrainingRequest(exercise_id=42, order_num=1, target_sets=3, target_reps=10, target_weight_pct=None)
    with pytest.raises(NotFoundError) as exc_info:
        await service.add_exercise_to_training(plan_id=1, training_id=2, user_id=1, payload=payload)

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "Exercise with id 42 not found"


async def test_delete_training_exercise_happy_path_calls_repository(repo: AsyncMock, service: ActivityService):
    repo.get_plan_by_id.return_value = _plan(1, author_id=1, title="Plan", is_public=False)
    repo.get_training_by_id.return_value = _training(2, plan_id=1, name="Day", order_num=1)
    pte = _plan_training_exercise(9, exercise_id=5, exercise_name="Row")
    pte.plan_training_id = 2
    repo.get_training_exercise_by_id.return_value = pte

    await service.delete_training_exercise(plan_id=1, training_id=2, pte_id=9, user_id=1)

    repo.delete_training_exercise.assert_awaited_once_with(pte)


async def test_delete_training_exercise_with_missing_link_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_plan_by_id.return_value = _plan(1, author_id=1, title="Plan", is_public=False)
    repo.get_training_by_id.return_value = _training(2, plan_id=1, name="Day", order_num=1)
    repo.get_training_exercise_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await service.delete_training_exercise(plan_id=1, training_id=2, pte_id=88, user_id=1)

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "PlanTrainingExercise with id 88 not found"


async def test_start_session_with_none_plan_training_id_returns_free_session(repo: AsyncMock, service: ActivityService):
    repo.create_session.return_value = _session(100, user_id=1, plan_training_id=None)

    result = await service.start_session(user_id=1, payload=StartSessionRequest(plan_training_id=None))

    repo.create_session.assert_awaited_once_with(user_id=1, plan_training_id=None)
    repo.add_exercise_to_session.assert_not_called()
    assert result.id == 100
    assert result.plan_training_id is None


async def test_start_session_with_template_populates_exercises_in_order(repo: AsyncMock, service: ActivityService):
    training = _training(
        5,
        plan_id=7,
        name="Template Day",
        exercises=[
            _plan_training_exercise(1, exercise_id=101, exercise_name="Second", order_num=2),
            _plan_training_exercise(2, exercise_id=100, exercise_name="First", order_num=1),
        ],
    )
    repo.get_training_with_exercises.return_value = training
    repo.get_plan_by_id.return_value = _plan(7, author_id=1, title="Public", is_public=True)
    repo.create_session.return_value = _session(101, user_id=1, plan_training_id=5)

    result = await service.start_session(user_id=1, payload=StartSessionRequest(plan_training_id=5))

    assert repo.add_exercise_to_session.await_count == 2
    first_call = repo.add_exercise_to_session.await_args_list[0].kwargs
    second_call = repo.add_exercise_to_session.await_args_list[1].kwargs
    assert first_call["exercise_id"] == 100
    assert first_call["order_num"] == 1
    assert first_call["is_from_template"] is True
    assert second_call["exercise_id"] == 101
    assert result.plan_training_id == 5


async def test_start_session_with_missing_training_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_training_with_exercises.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await service.start_session(user_id=1, payload=StartSessionRequest(plan_training_id=123))

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "PlanTraining with id 123 not found"


async def test_start_session_on_private_plan_by_non_owner_raises_forbidden(repo: AsyncMock, service: ActivityService):
    repo.get_training_with_exercises.return_value = _training(5, plan_id=7, name="Private")
    repo.get_plan_by_id.return_value = _plan(7, author_id=99, title="Private Plan", is_public=False)

    with pytest.raises(ForbiddenError) as exc_info:
        await service.start_session(user_id=1, payload=StartSessionRequest(plan_training_id=5))

    assert exc_info.value.error_code == "FORBIDDEN"
    assert exc_info.value.message == "This training belongs to a private plan"


async def test_end_session_happy_path_returns_ended_session(repo: AsyncMock, service: ActivityService):
    repo.get_session_by_id.return_value = _session(12, user_id=1, plan_training_id=None, ended_at=None)
    repo.end_session.return_value = _session(12, user_id=1, plan_training_id=None, ended_at=datetime(2026, 1, 1, 1, tzinfo=UTC))

    result = await service.end_session(session_id=12, user_id=1)

    assert result.id == 12
    assert result.ended_at is not None


@pytest.mark.parametrize(
    ("session", "error"),
    [
        (None, NotFoundError),
        (_session(12, user_id=2, plan_training_id=None), NotResourceOwnerError),
        (_session(12, user_id=1, plan_training_id=None, ended_at=datetime(2026, 1, 2, tzinfo=UTC)), SessionAlreadyEndedError),
    ],
)
async def test_end_session_error_paths_raise_expected_exception(
    repo: AsyncMock,
    service: ActivityService,
    session: SimpleNamespace | None,
    error: type[Exception],
):
    repo.get_session_by_id.return_value = session

    with pytest.raises(error):
        await service.end_session(session_id=12, user_id=1)


async def test_get_session_detail_happy_path_returns_nested_response(repo: AsyncMock, service: ActivityService):
    set_item = _workout_set(1, set_number=1, reps=5, weight=100.0)
    exercise_session = _exercise_session(
        exercise_session_id=2,
        workout_session_id=30,
        exercise_id=99,
        order_num=1,
        is_from_template=True,
        sets=[set_item],
        exercise_name="Squat",
    )
    repo.get_session_with_exercises.return_value = _session(
        session_id=30,
        user_id=1,
        plan_training_id=7,
        exercise_sessions=[exercise_session],
    )

    result = await service.get_session_detail(session_id=30, user_id=1)

    assert result.id == 30
    assert result.exercise_sessions[0].exercise_name == "Squat"
    assert result.exercise_sessions[0].sets[0].weight == 100.0


@pytest.mark.parametrize(
    ("session", "error"),
    [
        (None, NotFoundError),
        (_session(30, user_id=9, plan_training_id=None), ForbiddenError),
    ],
)
async def test_get_session_detail_error_paths_raise_expected_exception(
    repo: AsyncMock,
    service: ActivityService,
    session: SimpleNamespace | None,
    error: type[Exception],
):
    repo.get_session_with_exercises.return_value = session

    with pytest.raises(error):
        await service.get_session_detail(session_id=30, user_id=1)


async def test_list_user_sessions_returns_paginated_schema(repo: AsyncMock, service: ActivityService):
    repo.list_user_sessions.return_value = ([_session(1, user_id=3, plan_training_id=None)], 1)

    result = await service.list_user_sessions(user_id=3, page=1, size=20)

    assert result.total == 1
    assert result.page == 1
    assert result.items[0].user_id == 3


async def test_add_exercise_to_session_happy_path_returns_response(repo: AsyncMock, service: ActivityService):
    repo.get_session_by_id.return_value = _session(1, user_id=1, plan_training_id=None, ended_at=None)
    exercise = _exercise(7, "Lunge")
    repo.get_exercise_by_id.return_value = exercise
    repo.add_exercise_to_session.return_value = _exercise_session(
        exercise_session_id=4,
        workout_session_id=1,
        exercise_id=7,
        order_num=2,
        is_from_template=False,
        sets=[],
    )

    result = await service.add_exercise_to_session(
        session_id=1,
        user_id=1,
        payload=AddExerciseToSessionRequest(exercise_id=7, order_num=2),
    )

    assert result.id == 4
    assert result.exercise_name == "Lunge"
    assert result.is_from_template is False


@pytest.mark.parametrize(
    ("session", "error"),
    [
        (None, NotFoundError),
        (_session(1, user_id=8, plan_training_id=None), NotResourceOwnerError),
        (_session(1, user_id=1, plan_training_id=None, ended_at=datetime(2026, 1, 2, tzinfo=UTC)), SessionAlreadyEndedError),
    ],
)
async def test_add_exercise_to_session_with_invalid_session_state_raises(
    repo: AsyncMock,
    service: ActivityService,
    session: SimpleNamespace | None,
    error: type[Exception],
):
    repo.get_session_by_id.return_value = session

    with pytest.raises(error):
        await service.add_exercise_to_session(
            session_id=1,
            user_id=1,
            payload=AddExerciseToSessionRequest(exercise_id=7, order_num=1),
        )


async def test_add_exercise_to_session_with_missing_exercise_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_session_by_id.return_value = _session(1, user_id=1, plan_training_id=None)
    repo.get_exercise_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await service.add_exercise_to_session(
            session_id=1,
            user_id=1,
            payload=AddExerciseToSessionRequest(exercise_id=99, order_num=1),
        )

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "Exercise with id 99 not found"


async def test_add_set_when_weight_beats_existing_pr_upserts_record(repo: AsyncMock, service: ActivityService):
    repo.get_session_by_id.return_value = _session(1, user_id=1, plan_training_id=None)
    repo.get_exercise_session_by_id.return_value = _exercise_session(
        exercise_session_id=10,
        workout_session_id=1,
        exercise_id=55,
        order_num=1,
        is_from_template=False,
    )
    repo.add_set.return_value = _workout_set(3, set_number=1, reps=6, weight=120.0)
    repo.get_personal_record.return_value = _personal_record(2, user_id=1, exercise_id=55, exercise_name="Deadlift", weight=110.0)

    result = await service.add_set(
        session_id=1,
        exercise_session_id=10,
        user_id=1,
        payload=LogSetRequest(set_number=1, reps=6, weight=120.0),
    )

    repo.upsert_personal_record.assert_awaited_once_with(user_id=1, exercise_id=55, weight=120.0)
    assert result.id == 3
    assert result.weight == 120.0


async def test_add_set_with_zero_weight_does_not_upsert_personal_record(repo: AsyncMock, service: ActivityService):
    repo.get_session_by_id.return_value = _session(1, user_id=1, plan_training_id=None)
    repo.get_exercise_session_by_id.return_value = _exercise_session(
        exercise_session_id=10,
        workout_session_id=1,
        exercise_id=55,
        order_num=1,
        is_from_template=False,
    )
    repo.add_set.return_value = _workout_set(7, set_number=1, reps=15, weight=0.0)

    result = await service.add_set(
        session_id=1,
        exercise_session_id=10,
        user_id=1,
        payload=LogSetRequest(set_number=1, reps=15, weight=0.0),
    )

    repo.upsert_personal_record.assert_not_called()
    assert result.id == 7
    assert result.weight == 0.0


@pytest.mark.parametrize(
    ("session", "exercise_session", "error"),
    [
        (
            None,
            _exercise_session(10, workout_session_id=1, exercise_id=5, order_num=1, is_from_template=False),
            NotFoundError,
        ),
        (
            _session(1, user_id=2, plan_training_id=None),
            _exercise_session(10, workout_session_id=1, exercise_id=5, order_num=1, is_from_template=False),
            NotResourceOwnerError,
        ),
        (
            _session(1, user_id=1, plan_training_id=None, ended_at=datetime(2026, 1, 2, tzinfo=UTC)),
            _exercise_session(10, workout_session_id=1, exercise_id=5, order_num=1, is_from_template=False),
            SessionAlreadyEndedError,
        ),
        (_session(1, user_id=1, plan_training_id=None), None, NotFoundError),
    ],
)
async def test_add_set_error_paths_raise_expected_exception(
    repo: AsyncMock,
    service: ActivityService,
    session: SimpleNamespace | None,
    exercise_session: SimpleNamespace | None,
    error: type[Exception],
):
    repo.get_session_by_id.return_value = session
    repo.get_exercise_session_by_id.return_value = exercise_session

    with pytest.raises(error):
        await service.add_set(
            session_id=1,
            exercise_session_id=10,
            user_id=1,
            payload=LogSetRequest(set_number=1, reps=10, weight=50.0),
        )


async def test_list_personal_records_returns_response_list(repo: AsyncMock, service: ActivityService):
    repo.list_user_personal_records.return_value = [
        _personal_record(1, user_id=1, exercise_id=10, exercise_name="Bench", weight=100.0),
        _personal_record(2, user_id=1, exercise_id=11, exercise_name="Squat", weight=140.0),
    ]

    result = await service.list_personal_records(user_id=1)

    assert len(result) == 2
    assert result[0].exercise_name == "Bench"
    assert result[1].weight == 140.0


async def test_upsert_personal_record_happy_path_returns_response(repo: AsyncMock, service: ActivityService):
    repo.get_exercise_by_id.return_value = _exercise(8, "Deadlift")
    repo.get_personal_record.return_value = None
    upserted = _personal_record(3, user_id=1, exercise_id=8, exercise_name="Deadlift", weight=130.0)
    repo.upsert_personal_record.return_value = upserted
    repo.list_user_personal_records.return_value = [upserted]

    result = await service.upsert_personal_record(user_id=1, payload=UpsertPersonalRecordRequest(exercise_id=8, weight=130.0))

    repo.upsert_personal_record.assert_awaited_once_with(user_id=1, exercise_id=8, weight=130.0)
    assert result.id == 3
    assert result.weight == 130.0


async def test_upsert_personal_record_with_missing_exercise_raises_not_found(repo: AsyncMock, service: ActivityService):
    repo.get_exercise_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await service.upsert_personal_record(user_id=1, payload=UpsertPersonalRecordRequest(exercise_id=9, weight=100.0))

    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.message == "Exercise with id 9 not found"


async def test_upsert_personal_record_with_lower_weight_than_existing_raises_bad_request(repo: AsyncMock, service: ActivityService):
    repo.get_exercise_by_id.return_value = _exercise(9, "Bench")
    repo.get_personal_record.return_value = _personal_record(9, user_id=1, exercise_id=9, exercise_name="Bench", weight=120.0)

    with pytest.raises(BadRequestError) as exc_info:
        await service.upsert_personal_record(user_id=1, payload=UpsertPersonalRecordRequest(exercise_id=9, weight=110.0))

    assert exc_info.value.error_code == "BAD_REQUEST"
    assert "less than current record" in exc_info.value.message


async def test_delete_personal_record_happy_path_returns_deleted_id(repo: AsyncMock, service: ActivityService):
    repo.get_personal_record_by_id.return_value = _personal_record(20, user_id=1, exercise_id=7, exercise_name="Row", weight=80.0)

    result = await service.delete_personal_record(pr_id=20, user_id=1)

    repo.delete_personal_record.assert_awaited_once()
    assert result.deleted_pr_id == 20


@pytest.mark.parametrize(
    ("record", "error"),
    [
        (None, NotFoundError),
        (_personal_record(20, user_id=2, exercise_id=7, exercise_name="Row", weight=80.0), NotResourceOwnerError),
    ],
)
async def test_delete_personal_record_with_missing_or_non_owned_record_raises(
    repo: AsyncMock,
    service: ActivityService,
    record: SimpleNamespace | None,
    error: type[Exception],
):
    repo.get_personal_record_by_id.return_value = record

    with pytest.raises(error):
        await service.delete_personal_record(pr_id=20, user_id=1)
