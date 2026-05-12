import asyncio
from datetime import date

import pytest

import src.gamification.application.event_handlers as event_handlers
from src.gamification.application.event_handlers import register_gamification_handlers
from src.gamification.domain.xp_calculator import calculate_daily_norm_xp
from src.models.gamification import GamificationProfile
from src.nutrition.domain.events import DailyNormAchievedEvent, MealEntryAddedEvent
from src.shared.infrastructure.event_bus import EventBus


class FakeProfileRepository:
    def __init__(self, store: dict[int, GamificationProfile]) -> None:
        self._store = store

    async def get_by_user_id(self, user_id: int) -> GamificationProfile | None:
        return self._store.get(user_id)

    async def add(self, profile: GamificationProfile) -> None:
        if profile.total_xp is None:
            profile.total_xp = 0
        self._store[profile.user_id] = profile


class FakeGamificationUnitOfWork:
    def __init__(self, session, store: dict[int, GamificationProfile]) -> None:
        self._session = session
        self.profiles = FakeProfileRepository(store)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class FakeSession:
    def __init__(self, scalar_result):
        self._scalar_result = scalar_result

    async def scalar(self, _query):
        return self._scalar_result


class FakeSessionFactory:
    def __init__(self, scalar_result):
        self._scalar_result = scalar_result

    def __call__(self):
        return self

    async def __aenter__(self):
        return FakeSession(self._scalar_result)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


async def _wait_for_total_xp(store: dict[int, GamificationProfile], user_id: int, expected_xp: int, timeout_seconds: float = 1.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_seconds

    while asyncio.get_running_loop().time() < deadline:
        profile = store.get(user_id)
        if profile is not None and profile.total_xp == expected_xp:
            return
        await asyncio.sleep(0.01)

    profile = store.get(user_id)
    actual_xp = None if profile is None else profile.total_xp
    assert actual_xp == expected_xp


@pytest.mark.asyncio
async def test_meal_entry_add_awards_xp_via_gamification_handler(monkeypatch):
    store: dict[int, GamificationProfile] = {}
    monkeypatch.setattr(event_handlers, "GamificationUnitOfWork", lambda session: FakeGamificationUnitOfWork(session, store))

    bus = EventBus()
    register_gamification_handlers(bus, FakeSessionFactory(scalar_result=1))

    await bus.publish(
        MealEntryAddedEvent(
            user_id=1,
            diary_id=10,
            meal_entry_id=100,
            food_id=20,
            meal_type="breakfast",
            weight_grams=50.0,
            target_date=date(2026, 4, 7),
        )
    )
    await _wait_for_total_xp(store, 1, 10)


@pytest.mark.asyncio
async def test_third_meal_of_day_applies_bonus_xp(monkeypatch):
    store: dict[int, GamificationProfile] = {}
    monkeypatch.setattr(event_handlers, "GamificationUnitOfWork", lambda session: FakeGamificationUnitOfWork(session, store))

    bus = EventBus()
    register_gamification_handlers(bus, FakeSessionFactory(scalar_result=3))

    await bus.publish(
        MealEntryAddedEvent(
            user_id=2,
            diary_id=11,
            meal_entry_id=101,
            food_id=21,
            meal_type="lunch",
            weight_grams=40.0,
            target_date=date(2026, 4, 8),
        )
    )
    await _wait_for_total_xp(store, 2, 40)


@pytest.mark.asyncio
async def test_daily_norm_event_awards_once_per_day(monkeypatch, fake_redis):
    store: dict[int, GamificationProfile] = {}
    monkeypatch.setattr(event_handlers, "GamificationUnitOfWork", lambda session: FakeGamificationUnitOfWork(session, store))
    monkeypatch.setattr(event_handlers.redis_module, "get_redis", lambda: fake_redis)

    bus = EventBus()
    register_gamification_handlers(bus, FakeSessionFactory(scalar_result=None))

    event = DailyNormAchievedEvent(user_id=3, diary_id=12, target_date=date(2026, 4, 9))

    await bus.publish(event)
    await _wait_for_total_xp(store, 3, calculate_daily_norm_xp())

    await bus.publish(event)
    await _wait_for_total_xp(store, 3, calculate_daily_norm_xp())
