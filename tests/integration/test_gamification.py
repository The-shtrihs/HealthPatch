import asyncio
from datetime import date

import pytest

import src.core_context.gamification.application.event_handlers as event_handlers
from src.core_context.gamification.application.event_handlers import register_gamification_handlers
from src.core_context.gamification.domain.xp_calculator import calculate_daily_norm_xp
from src.core_context.nutrition.contracts.events import DailyNormAchieved, MealEntryAdded
from src.shared.infrastructure.daily_claim_store import DailyClaimStore
from src.shared.infrastructure.event_bus import EventBus


class FakeProfileRepository:
    def __init__(self, store: dict[int, int]) -> None:
        self._store = store

    async def ensure_profile(self, user_id: int) -> None:
        self._store.setdefault(user_id, 0)

    async def award_xp(self, user_id: int, xp: int) -> int:
        self._store[user_id] = self._store.get(user_id, 0) + xp
        return self._store[user_id]


class FakeGamificationUnitOfWork:
    def __init__(self, session, store: dict[int, int]) -> None:
        self._session = session
        self.profiles = FakeProfileRepository(store)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class FakeSession:
    pass


class FakeSessionFactory:
    def __call__(self):
        return self

    async def __aenter__(self):
        return FakeSession()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class FakeDailyClaimStore(DailyClaimStore):
    def __init__(self) -> None:
        self._claims: set[tuple[int, date]] = set()

    async def try_claim(self, user_id: int, target_date) -> bool:
        key = (user_id, target_date)
        if key in self._claims:
            return False
        self._claims.add(key)
        return True


class FakeMealEntryQueries:
    def __init__(self, count: int = 0) -> None:
        self._count = count

    async def count_for_day(self, user_id: int, day) -> int:
        return self._count


async def _wait_for_total_xp(store: dict[int, int], user_id: int, expected_xp: int, timeout_seconds: float = 1.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_seconds

    while asyncio.get_running_loop().time() < deadline:
        total_xp = store.get(user_id)
        if total_xp == expected_xp:
            return
        await asyncio.sleep(0.01)

    assert store.get(user_id) == expected_xp


@pytest.mark.asyncio
async def test_meal_entry_add_awards_xp_via_gamification_handler(monkeypatch):
    store: dict[int, int] = {}
    monkeypatch.setattr(event_handlers, "GamificationUnitOfWork", lambda session: FakeGamificationUnitOfWork(session, store))

    bus = EventBus()
    register_gamification_handlers(bus, FakeSessionFactory(), FakeMealEntryQueries(count=1), FakeDailyClaimStore())

    await bus.publish(
        MealEntryAdded(
            entry_id=100,
            user_id=1,
            consumed_on=date(2026, 4, 7),
            meal_type="breakfast",
            weight_grams=50.0,
        )
    )
    await _wait_for_total_xp(store, 1, 10)


@pytest.mark.asyncio
async def test_third_meal_of_day_applies_bonus_xp(monkeypatch):
    store: dict[int, int] = {}
    monkeypatch.setattr(event_handlers, "GamificationUnitOfWork", lambda session: FakeGamificationUnitOfWork(session, store))

    bus = EventBus()
    register_gamification_handlers(bus, FakeSessionFactory(), FakeMealEntryQueries(count=3), FakeDailyClaimStore())

    await bus.publish(
        MealEntryAdded(
            entry_id=101,
            user_id=2,
            consumed_on=date(2026, 4, 8),
            meal_type="lunch",
            weight_grams=40.0,
        )
    )
    await _wait_for_total_xp(store, 2, 40)


@pytest.mark.asyncio
async def test_daily_norm_event_awards_once_per_day(monkeypatch):
    store: dict[int, int] = {}
    monkeypatch.setattr(event_handlers, "GamificationUnitOfWork", lambda session: FakeGamificationUnitOfWork(session, store))

    bus = EventBus()
    register_gamification_handlers(bus, FakeSessionFactory(), FakeMealEntryQueries(), FakeDailyClaimStore())

    event = DailyNormAchieved(user_id=3, day=date(2026, 4, 9))

    await bus.publish(event)
    await _wait_for_total_xp(store, 3, calculate_daily_norm_xp())

    await bus.publish(event)
    await _wait_for_total_xp(store, 3, calculate_daily_norm_xp())
