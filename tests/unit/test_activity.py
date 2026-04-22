"""Unit tests for the activity domain.

These tests cover pure domain behavior + application use cases using in-memory fakes.
They do NOT boot a database, a FastAPI app, or a Redis pool — which demonstrates
the layering rules required by Lab 2.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.activity.application.dto import (
    AddExerciseToSessionCommand,
    AddTrainingCommand,
    CreateExerciseCommand,
    CreateMuscleGroupCommand,
    CreateWorkoutPlanCommand,
    DeletePersonalRecordCommand,
    DeleteWorkoutPlanCommand,
    EndSessionCommand,
    ListExercisesQuery,
    LogSetCommand,
    PlanTrainingExerciseInput,
    PlanTrainingInput,
    StartSessionCommand,
    UpdateWorkoutPlanCommand,
    UpsertPersonalRecordCommand,
)
from src.activity.application.use_cases.exercise_catalog import (
    CreateExerciseUseCase,
    CreateMuscleGroupUseCase,
    GetExerciseUseCase,
    ListExercisesUseCase,
    ListMuscleGroupsUseCase,
)
from src.activity.application.use_cases.personal_record import (
    DeletePersonalRecordUseCase,
    ListPersonalRecordsUseCase,
    UpsertPersonalRecordUseCase,
)
from src.activity.application.use_cases.workout_plan import (
    AddTrainingUseCase,
    CreatePlanUseCase,
    DeletePlanUseCase,
    GetPlanUseCase,
    UpdatePlanUseCase,
)
from src.activity.application.use_cases.workout_session import (
    AddExerciseToSessionUseCase,
    EndSessionUseCase,
    LogSetUseCase,
    StartSessionUseCase,
)
from src.activity.domain.errors import (
    ExerciseNotFoundError,
    InvalidPlanTitleError,
    InvalidRepsError,
    InvalidSetNumberError,
    InvalidTimeRangeError,
    InvalidWeightError,
    MuscleGroupNotFoundError,
    NotResourceOwnerError,
    PersonalRecordDowngradeError,
    PersonalRecordNotFoundError,
    PrivatePlanAccessError,
    SessionAlreadyEndedError,
    WorkoutPlanNotFoundError,
    WorkoutSessionNotFoundError,
)
from src.activity.domain.factory import (
    PersonalRecordFactory,
    WorkoutPlanFactory,
    WorkoutSessionFactory,
    WorkoutSetFactory,
)
from src.activity.domain.interfaces import IActivityRepository, IActivityUnitOfWork
from src.activity.domain.models import (
    ExerciseDomain,
    ExerciseSessionDomain,
    MuscleGroupDomain,
    PersonalRecordDomain,
    PlanTrainingDomain,
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

class FakeActivityRepository(IActivityRepository):

    def __init__(self) -> None:
        self._muscle_groups: dict[int, MuscleGroupDomain] = {}
        self._exercises: dict[int, ExerciseDomain] = {}
        self._plans: dict[int, WorkoutPlanDomain] = {}
        self._trainings: dict[int, PlanTrainingDomain] = {}
        self._ptes: dict[int, PlanTrainingExerciseDomain] = {}
        self._sessions: dict[int, WorkoutSessionDomain] = {}
        self._exercise_sessions: dict[int, ExerciseSessionDomain] = {}
        self._sets: dict[int, WorkoutSetDomain] = {}
        self._prs: dict[int, PersonalRecordDomain] = {}
        self._next_id = 1

    def _pop_id(self) -> int:
        n = self._next_id
        self._next_id += 1
        return n

    async def list_muscle_groups(self) -> list[MuscleGroupDomain]:
        return list(self._muscle_groups.values())

    async def get_muscle_group_by_id(self, muscle_group_id: int):
        return self._muscle_groups.get(muscle_group_id)

    async def create_muscle_group(self, name: str):
        mg = MuscleGroupDomain(id=self._pop_id(), name=name)
        self._muscle_groups[mg.id] = mg
        return mg

    async def get_exercise_by_id(self, exercise_id: int):
        return self._exercises.get(exercise_id)

    async def list_exercises(self, search, offset, limit):
        items = list(self._exercises.values())
        if search:
            items = [e for e in items if search.lower() in e.name.lower()]
        return items[offset : offset + limit], len(items)

    async def create_exercise(self, name, primary_muscle_group_id, secondary_muscle_group_ids):
        primary = self._muscle_groups.get(primary_muscle_group_id) if primary_muscle_group_id else None
        secondary = [self._muscle_groups[i] for i in secondary_muscle_group_ids if i in self._muscle_groups]
        ex = ExerciseDomain(id=self._pop_id(), name=name, primary_muscle_group=primary, secondary_muscle_groups=secondary)
        self._exercises[ex.id] = ex
        return ex
    
    async def get_plan_by_id(self, plan_id):
        return self._plans.get(plan_id)

    async def get_plan_with_trainings(self, plan_id):
        p = self._plans.get(plan_id)
        if p is None:
            return None
        trainings = [t for t in self._trainings.values() if t.plan_id == plan_id]
        for t in trainings:
            t.exercises = [pte for pte in self._ptes.values() if pte.plan_training_id == t.id]
        p.trainings = trainings
        return p

    async def list_public_plans(self, offset, limit):
        items = [p for p in self._plans.values() if p.is_public]
        return items[offset : offset + limit], len(items)

    async def list_user_plans(self, user_id, offset, limit):
        items = [p for p in self._plans.values() if p.author_id == user_id]
        return items[offset : offset + limit], len(items)

    async def create_plan(self, author_id, title, description, is_public):
        p = WorkoutPlanDomain(
            id=self._pop_id(),
            author_id=author_id,
            title=title,
            description=description,
            is_public=is_public,
        )
        self._plans[p.id] = p
        return p

    async def save_plan(self, plan):
        if plan.id is None or plan.id not in self._plans:
            raise WorkoutPlanNotFoundError(plan.id)
        self._plans[plan.id] = plan
        return plan

    async def delete_plan(self, plan_id):
        if plan_id not in self._plans:
            raise WorkoutPlanNotFoundError(plan_id)
        del self._plans[plan_id]

    async def get_training_by_id(self, training_id):
        return self._trainings.get(training_id)

    async def get_training_with_exercises(self, training_id):
        t = self._trainings.get(training_id)
        if t is None:
            return None
        t.exercises = [p for p in self._ptes.values() if p.plan_training_id == training_id]
        return t

    async def add_training(self, plan_id, name, weekday, order_num):
        t = PlanTrainingDomain(
            id=self._pop_id(),
            plan_id=plan_id,
            name=name,
            weekday=weekday,
            order_num=order_num,
        )
        self._trainings[t.id] = t
        return t

    async def delete_training(self, training_id):
        self._trainings.pop(training_id, None)

    async def get_training_exercise_by_id(self, pte_id):
        return self._ptes.get(pte_id)

    async def add_exercise_to_training(self, plan_training_id, exercise_id, order_num, target_sets, target_reps, target_weight_pct):
        ex = self._exercises.get(exercise_id)
        pte = PlanTrainingExerciseDomain(
            id=self._pop_id(),
            plan_training_id=plan_training_id,
            exercise_id=exercise_id,
            exercise_name=ex.name if ex else None,
            order_num=order_num,
            target_sets=target_sets,
            target_reps=target_reps,
            target_weight_pct=target_weight_pct,
        )
        self._ptes[pte.id] = pte
        return pte

    async def delete_training_exercise(self, pte_id):
        self._ptes.pop(pte_id, None)

    async def get_session_by_id(self, session_id):
        return self._sessions.get(session_id)

    async def get_session_with_exercises(self, session_id):
        s = self._sessions.get(session_id)
        if s is None:
            return None
        s.exercise_sessions = [es for es in self._exercise_sessions.values() if es.workout_session_id == session_id]
        return s

    async def list_user_sessions(self, user_id, offset, limit):
        items = [s for s in self._sessions.values() if s.user_id == user_id]
        return items[offset : offset + limit], len(items)

    async def create_session(self, user_id, plan_training_id, started_at):
        s = WorkoutSessionDomain(
            id=self._pop_id(),
            user_id=user_id,
            plan_training_id=plan_training_id,
            time_range=TimeRange(started_at=started_at, ended_at=None),
        )
        self._sessions[s.id] = s
        return s

    async def save_session(self, session):
        if session.id is None or session.id not in self._sessions:
            raise WorkoutSessionNotFoundError(session.id)
        self._sessions[session.id] = session
        return session

    async def get_exercise_session_by_id(self, exercise_session_id):
        return self._exercise_sessions.get(exercise_session_id)

    async def add_exercise_to_session(self, workout_session_id, exercise_id, order_num, is_from_template):
        ex = self._exercises.get(exercise_id)
        es = ExerciseSessionDomain(
            id=self._pop_id(),
            workout_session_id=workout_session_id,
            exercise_id=exercise_id,
            exercise_name=ex.name if ex else None,
            order_num=order_num,
            is_from_template=is_from_template,
        )
        self._exercise_sessions[es.id] = es
        return es

    # sets
    async def add_set(self, exercise_session_id, set_number, reps, weight):
        ws = WorkoutSetDomain(
            id=self._pop_id(),
            exercise_session_id=exercise_session_id,
            set_number=SetNumber(set_number),
            reps=RepCount(reps),
            weight=WeightKg(weight),
        )
        self._sets[ws.id] = ws
        return ws

    # PRs
    async def get_personal_record(self, user_id, exercise_id):
        for pr in self._prs.values():
            if pr.user_id == user_id and pr.exercise_id == exercise_id:
                return pr
        return None

    async def get_personal_record_by_id(self, pr_id):
        return self._prs.get(pr_id)

    async def list_user_personal_records(self, user_id):
        return [pr for pr in self._prs.values() if pr.user_id == user_id]

    async def upsert_personal_record(self, user_id, exercise_id, weight, recorded_at):
        existing = await self.get_personal_record(user_id, exercise_id)
        if existing is None:
            pr = PersonalRecordDomain(
                id=self._pop_id(),
                user_id=user_id,
                exercise_id=exercise_id,
                exercise_name=self._exercises.get(exercise_id).name if exercise_id in self._exercises else None,
                weight=WeightKg(weight),
                recorded_at=recorded_at,
            )
            self._prs[pr.id] = pr
            return pr
        existing.weight = WeightKg(weight)
        existing.recorded_at = recorded_at
        return existing

    async def delete_personal_record(self, pr_id):
        if pr_id not in self._prs:
            raise PersonalRecordNotFoundError(pr_id)
        del self._prs[pr_id]


class FakeUnitOfWork(IActivityUnitOfWork):
    def __init__(self, repo: FakeActivityRepository):
        self.repo = repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.fixture
def repo() -> FakeActivityRepository:
    return FakeActivityRepository()


@pytest.fixture
def uow(repo) -> FakeUnitOfWork:
    return FakeUnitOfWork(repo)


class TestValueObjects:
    def test_weight_rejects_negative(self):
        with pytest.raises(InvalidWeightError):
            WeightKg(-1.0)

    def test_weight_allows_zero(self):
        assert WeightKg(0).value == 0

    def test_reps_rejects_zero_or_negative(self):
        with pytest.raises(InvalidRepsError):
            RepCount(0)

    def test_set_number_rejects_zero(self):
        with pytest.raises(InvalidSetNumberError):
            SetNumber(0)

    def test_time_range_rejects_end_before_start(self):
        now = datetime.now(UTC)
        with pytest.raises(InvalidTimeRangeError):
            TimeRange(started_at=now, ended_at=now - timedelta(minutes=1))

    def test_time_range_duration(self):
        start = datetime.now(UTC)
        tr = TimeRange(started_at=start, ended_at=start + timedelta(minutes=30))
        assert tr.duration_minutes() == 30

class TestWorkoutPlanDomain:
    def test_requires_non_empty_title(self):
        with pytest.raises(InvalidPlanTitleError):
            WorkoutPlanDomain(id=None, author_id=1, title="   ", description=None, is_public=False)

    def test_update_details_enforces_title(self):
        plan = WorkoutPlanDomain(id=1, author_id=1, title="Old", description=None, is_public=False)
        with pytest.raises(InvalidPlanTitleError):
            plan.update_details(title="  ")

    def test_is_visible_respects_public_flag(self):
        plan = WorkoutPlanDomain(id=1, author_id=1, title="T", description=None, is_public=True)
        assert plan.is_visible_to(user_id=99) is True

    def test_is_visible_respects_author(self):
        plan = WorkoutPlanDomain(id=1, author_id=1, title="T", description=None, is_public=False)
        assert plan.is_visible_to(user_id=1) is True
        assert plan.is_visible_to(user_id=99) is False


class TestWorkoutSessionDomain:
    def test_end_sets_ended_at(self):
        start = datetime.now(UTC)
        s = WorkoutSessionDomain(
            id=1,
            user_id=1,
            plan_training_id=None,
            time_range=TimeRange(started_at=start),
        )
        s.end(at=start + timedelta(minutes=45))
        assert s.is_ended
        assert s.duration_minutes() == 45

    def test_cannot_end_already_ended(self):
        start = datetime.now(UTC)
        s = WorkoutSessionDomain(
            id=1,
            user_id=1,
            plan_training_id=None,
            time_range=TimeRange(started_at=start, ended_at=start + timedelta(minutes=1)),
        )
        with pytest.raises(SessionAlreadyEndedError):
            s.end(at=datetime.now(UTC))

    def test_ensure_can_be_modified_raises_when_ended(self):
        start = datetime.now(UTC)
        s = WorkoutSessionDomain(
            id=1,
            user_id=1,
            plan_training_id=None,
            time_range=TimeRange(started_at=start, ended_at=start),
        )
        with pytest.raises(SessionAlreadyEndedError):
            s.ensure_can_be_modified()



class TestWorkoutPlanFactory:
    def test_creates_valid_plan(self):
        f = WorkoutPlanFactory()
        plan = f.create(author_id=1, title="Plan", description=None, is_public=False)
        assert plan.id is None
        assert plan.author_id == 1

    def test_rejects_empty_title(self):
        f = WorkoutPlanFactory()
        with pytest.raises(InvalidPlanTitleError):
            f.create(author_id=1, title=" ", description=None, is_public=False)


@pytest.mark.asyncio
class TestPersonalRecordFactory:
    async def test_rejects_downgrade(self, repo: FakeActivityRepository):
        mg = await repo.create_muscle_group("chest")
        ex = await repo.create_exercise("bench", mg.id, [])
        now = datetime.now(UTC)
        await repo.upsert_personal_record(user_id=1, exercise_id=ex.id, weight=100, recorded_at=now)
        f = PersonalRecordFactory(repo)
        with pytest.raises(PersonalRecordDowngradeError):
            await f.upsert(user_id=1, exercise_id=ex.id, weight=90, at=now)

    async def test_rejects_unknown_exercise(self, repo: FakeActivityRepository):
        f = PersonalRecordFactory(repo)
        with pytest.raises(ExerciseNotFoundError):
            await f.upsert(user_id=1, exercise_id=999, weight=50, at=datetime.now(UTC))


@pytest.mark.asyncio
class TestWorkoutSetFactory:
    async def test_rejects_when_session_ended(self, repo: FakeActivityRepository):
        mg = await repo.create_muscle_group("chest")
        ex = await repo.create_exercise("bench", mg.id, [])
        start = datetime.now(UTC)
        s = await repo.create_session(user_id=1, plan_training_id=None, started_at=start)
        s.end(at=start + timedelta(minutes=30))
        await repo.save_session(s)
        es = await repo.add_exercise_to_session(workout_session_id=s.id, exercise_id=ex.id, order_num=1, is_from_template=False)
        f = WorkoutSetFactory(repo)
        with pytest.raises(SessionAlreadyEndedError):
            await f.log(exercise_session_id=es.id, set_number=1, reps=5, weight=50)


@pytest.mark.asyncio
class TestWorkoutSessionFactory:
    async def test_rejects_unknown_training(self, repo: FakeActivityRepository):
        f = WorkoutSessionFactory(repo)
        from src.activity.domain.errors import PlanTrainingNotFoundError

        with pytest.raises(PlanTrainingNotFoundError):
            await f.start(user_id=1, plan_training_id=999, at=datetime.now(UTC))



async def _seed_user_and_exercise(repo: FakeActivityRepository):
    mg = await repo.create_muscle_group("chest")
    ex = await repo.create_exercise("bench", mg.id, [])
    return mg, ex


@pytest.mark.asyncio
class TestExerciseCatalog:
    async def test_list_muscle_groups_empty(self, uow):
        result = await ListMuscleGroupsUseCase(uow).execute()
        assert result == []

    async def test_create_muscle_group(self, uow):
        mg = await CreateMuscleGroupUseCase(uow).execute(CreateMuscleGroupCommand(name="  Back  "))
        assert mg.name == "Back"
        assert mg.id is not None

    async def test_create_exercise_rejects_missing_mg(self, uow):
        with pytest.raises(MuscleGroupNotFoundError):
            await CreateExerciseUseCase(uow).execute(CreateExerciseCommand(name="Squat", primary_muscle_group_id=999, secondary_muscle_group_ids=[]))

    async def test_get_exercise_404(self, uow):
        with pytest.raises(ExerciseNotFoundError):
            await GetExerciseUseCase(uow).execute(exercise_id=999)

    async def test_list_exercises_pagination(self, uow, repo):
        mg = await repo.create_muscle_group("chest")
        for i in range(5):
            await repo.create_exercise(f"ex{i}", mg.id, [])
        page = await ListExercisesUseCase(uow).execute(ListExercisesQuery(search=None, page=1, size=2))
        assert page.total == 5
        assert len(page.items) == 2


@pytest.mark.asyncio
class TestWorkoutPlan:
    async def test_create_plan_with_training(self, uow, repo):
        _, ex = await _seed_user_and_exercise(repo)
        cmd = CreateWorkoutPlanCommand(
            author_id=1,
            title="My Plan",
            description=None,
            is_public=False,
            trainings=[
                PlanTrainingInput(
                    name="Day 1",
                    order_num=1,
                    weekday=Weekday.MON,
                    exercises=[PlanTrainingExerciseInput(exercise_id=ex.id, order_num=1, target_sets=3, target_reps=10, target_weight_pct=None)],
                )
            ],
        )
        plan = await CreatePlanUseCase(uow).execute(cmd)
        assert plan.title == "My Plan"
        assert len(plan.trainings) == 1
        assert plan.trainings[0].exercises[0].exercise_id == ex.id

    async def test_create_plan_rejects_unknown_exercise(self, uow):
        cmd = CreateWorkoutPlanCommand(
            author_id=1,
            title="P",
            description=None,
            is_public=False,
            trainings=[
                PlanTrainingInput(
                    name="Day 1",
                    order_num=1,
                    weekday=None,
                    exercises=[PlanTrainingExerciseInput(exercise_id=999, order_num=1, target_sets=3, target_reps=10, target_weight_pct=None)],
                )
            ],
        )
        with pytest.raises(ExerciseNotFoundError):
            await CreatePlanUseCase(uow).execute(cmd)

    async def test_update_plan_checks_ownership(self, uow, repo):
        plan = await repo.create_plan(author_id=1, title="P", description=None, is_public=False)
        with pytest.raises(NotResourceOwnerError):
            await UpdatePlanUseCase(uow).execute(UpdateWorkoutPlanCommand(plan_id=plan.id, user_id=2, title="X", description=None, is_public=None))

    async def test_delete_plan_404(self, uow):
        with pytest.raises(WorkoutPlanNotFoundError):
            await DeletePlanUseCase(uow).execute(DeleteWorkoutPlanCommand(plan_id=999, user_id=1))

    async def test_get_plan_private_forbidden(self, uow, repo):
        plan = await repo.create_plan(author_id=1, title="P", description=None, is_public=False)
        with pytest.raises(PrivatePlanAccessError):
            await GetPlanUseCase(uow).execute(plan_id=plan.id, requesting_user_id=2)

    async def test_add_training_ownership(self, uow, repo):
        plan = await repo.create_plan(author_id=1, title="P", description=None, is_public=False)
        with pytest.raises(NotResourceOwnerError):
            await AddTrainingUseCase(uow).execute(AddTrainingCommand(plan_id=plan.id, user_id=2, name="D", weekday=None, order_num=1))


@pytest.mark.asyncio
class TestWorkoutSession:
    async def test_start_session_no_training(self, uow):
        s = await StartSessionUseCase(uow).execute(StartSessionCommand(user_id=1, plan_training_id=None))
        assert s.user_id == 1
        assert not s.is_ended

    async def test_end_session_ownership(self, uow, repo):
        start = datetime.now(UTC)
        s = await repo.create_session(user_id=1, plan_training_id=None, started_at=start)
        with pytest.raises(NotResourceOwnerError):
            await EndSessionUseCase(uow).execute(EndSessionCommand(session_id=s.id, user_id=2))

    async def test_end_session_conflict_when_already_ended(self, uow, repo):
        start = datetime.now(UTC)
        s = await repo.create_session(user_id=1, plan_training_id=None, started_at=start)
        s.end(at=start + timedelta(minutes=1))
        await repo.save_session(s)
        with pytest.raises(SessionAlreadyEndedError):
            await EndSessionUseCase(uow).execute(EndSessionCommand(session_id=s.id, user_id=1))

    async def test_log_set_updates_personal_record(self, uow, repo):
        _, ex = await _seed_user_and_exercise(repo)
        start = datetime.now(UTC)
        sess = await repo.create_session(user_id=1, plan_training_id=None, started_at=start)
        es = await repo.add_exercise_to_session(workout_session_id=sess.id, exercise_id=ex.id, order_num=1, is_from_template=False)
        await LogSetUseCase(uow).execute(
            LogSetCommand(
                session_id=sess.id,
                exercise_session_id=es.id,
                user_id=1,
                set_number=1,
                reps=5,
                weight=80,
            )
        )
        pr = await repo.get_personal_record(user_id=1, exercise_id=ex.id)
        assert pr is not None
        assert pr.weight.value == 80

    async def test_add_exercise_to_ended_session_conflicts(self, uow, repo):
        _, ex = await _seed_user_and_exercise(repo)
        start = datetime.now(UTC)
        sess = await repo.create_session(user_id=1, plan_training_id=None, started_at=start)
        sess.end(at=start + timedelta(minutes=1))
        await repo.save_session(sess)
        with pytest.raises(SessionAlreadyEndedError):
            await AddExerciseToSessionUseCase(uow).execute(AddExerciseToSessionCommand(session_id=sess.id, user_id=1, exercise_id=ex.id, order_num=1))


@pytest.mark.asyncio
class TestPersonalRecord:
    async def test_upsert_rejects_downgrade(self, uow, repo):
        _, ex = await _seed_user_and_exercise(repo)
        await repo.upsert_personal_record(user_id=1, exercise_id=ex.id, weight=100, recorded_at=datetime.now(UTC))
        with pytest.raises(PersonalRecordDowngradeError):
            await UpsertPersonalRecordUseCase(uow).execute(UpsertPersonalRecordCommand(user_id=1, exercise_id=ex.id, weight=90))

    async def test_upsert_creates_new_record(self, uow, repo):
        _, ex = await _seed_user_and_exercise(repo)
        pr = await UpsertPersonalRecordUseCase(uow).execute(UpsertPersonalRecordCommand(user_id=1, exercise_id=ex.id, weight=75))
        assert pr.weight.value == 75

    async def test_delete_pr_ownership(self, uow, repo):
        _, ex = await _seed_user_and_exercise(repo)
        pr = await repo.upsert_personal_record(user_id=1, exercise_id=ex.id, weight=80, recorded_at=datetime.now(UTC))
        with pytest.raises(NotResourceOwnerError):
            await DeletePersonalRecordUseCase(uow).execute(DeletePersonalRecordCommand(pr_id=pr.id, user_id=2))

    async def test_list_prs_scopes_to_user(self, uow, repo):
        _, ex = await _seed_user_and_exercise(repo)
        await repo.upsert_personal_record(user_id=1, exercise_id=ex.id, weight=80, recorded_at=datetime.now(UTC))
        await repo.upsert_personal_record(user_id=2, exercise_id=ex.id, weight=70, recorded_at=datetime.now(UTC))
        mine = await ListPersonalRecordsUseCase(uow).execute(user_id=1)
        assert len(mine) == 1