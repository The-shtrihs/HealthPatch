from datetime import date
from unittest.mock import AsyncMock

import pytest

from src.core_context.nutrition.application.commands import AddMealEntryCommand, DeleteMealEntryCommand, UpdateDailyDiaryCommand
from src.core_context.nutrition.application.handlers.add_meal_entry import AddMealEntryCommandHandler
from src.core_context.nutrition.application.handlers.delete_meal_entry import DeleteMealEntryCommandHandler
from src.core_context.nutrition.application.handlers.get_daily_norm import GetDailyNormQueryHandler
from src.core_context.nutrition.application.handlers.get_day_overview import GetDayOverviewQueryHandler
from src.core_context.nutrition.application.handlers.update_daily_diary import UpdateDailyDiaryCommandHandler
from src.core_context.nutrition.application.queries import GetDailyNormQuery, GetDayOverviewQuery
from src.core_context.nutrition.domain.calculations import calculate_daily_norm
from src.core_context.nutrition.domain.errors import (
    IncompleteNutritionProfileError,
    InvalidMealEntryError,
    MealEntryNotFoundError,
    NutritionProfileNotFoundError,
)
from src.core_context.nutrition.domain.events import DailyDiaryUpdatedEvent, MealEntryAddedEvent, MealEntryDeletedEvent
from src.core_context.nutrition.domain.interfaces import INutritionReadRepository, INutritionRepository
from src.core_context.nutrition.domain.models import MacroTotalsDomain, NutritionProfileDomain
from src.core_context.user.domain.models import FitnessGoal, Gender
from src.shared.infrastructure.event_bus_interface import IEventBus


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock(spec=INutritionRepository)


@pytest.fixture
def read_repo() -> AsyncMock:
    return AsyncMock(spec=INutritionReadRepository)


@pytest.fixture
def event_bus() -> AsyncMock:
    return AsyncMock(spec=IEventBus)


@pytest.fixture
def uow(repo: AsyncMock) -> AsyncMock:
    uow = AsyncMock()
    uow.repo = repo
    uow.events = []
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False
    return uow


@pytest.fixture
def add_meal_entry_handler(uow: AsyncMock, event_bus: AsyncMock) -> AddMealEntryCommandHandler:
    return AddMealEntryCommandHandler(uow, event_bus)


@pytest.fixture
def delete_meal_entry_handler(uow: AsyncMock, event_bus: AsyncMock) -> DeleteMealEntryCommandHandler:
    return DeleteMealEntryCommandHandler(uow, event_bus)


@pytest.fixture
def update_daily_diary_handler(uow: AsyncMock, event_bus: AsyncMock) -> UpdateDailyDiaryCommandHandler:
    return UpdateDailyDiaryCommandHandler(uow, event_bus)


@pytest.fixture
def get_daily_norm_handler(read_repo: AsyncMock) -> GetDailyNormQueryHandler:
    return GetDailyNormQueryHandler(read_repo)


@pytest.fixture
def get_day_overview_handler(read_repo: AsyncMock) -> GetDayOverviewQueryHandler:
    return GetDayOverviewQueryHandler(read_repo)


def _valid_profile():
    return NutritionProfileDomain(
        age=30,
        weight=80.0,
        height=180.0,
        gender=Gender.MALE,
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
    )


@pytest.mark.asyncio
async def test_get_day_overview_calculates_remaining_and_floors_zero(get_day_overview_handler: GetDayOverviewQueryHandler, read_repo: AsyncMock):
    profile = _valid_profile()
    read_repo.get_profile.return_value = profile

    norm = calculate_daily_norm(profile)
    read_repo.get_day_consumed_totals.return_value = MacroTotalsDomain(
        calories=norm.calories + 50.0,
        protein_g=norm.protein_g + 10.0,
        fat_g=max(0.0, norm.fat_g - 20.0),
        carbs_g=max(0.0, norm.carbs_g - 30.0),
    )

    out = await get_day_overview_handler.handle(GetDayOverviewQuery(user_id=1, target_date=date(2026, 4, 7)))

    assert out.remaining.calories == 0.0
    assert out.remaining.protein_g == 0.0
    assert out.remaining.fat_g > 0
    assert out.remaining.carbs_g > 0


@pytest.mark.asyncio
async def test_add_meal_entry_rejects_non_positive_weight(add_meal_entry_handler: AddMealEntryCommandHandler):
    with pytest.raises(InvalidMealEntryError) as exc:
        await add_meal_entry_handler.handle(
            AddMealEntryCommand(
                user_id=1,
                food_id=10,
                meal_type="lunch",
                weight_grams=0,
            )
        )
    assert "greater than 0" in exc.value.message


@pytest.mark.asyncio
async def test_add_meal_entry_rejects_blank_meal_type(add_meal_entry_handler: AddMealEntryCommandHandler):
    with pytest.raises(InvalidMealEntryError) as exc:
        await add_meal_entry_handler.handle(
            AddMealEntryCommand(
                user_id=1,
                food_id=10,
                meal_type="   ",
                weight_grams=120,
            )
        )
    assert "Meal type is required" in exc.value.message


@pytest.mark.asyncio
async def test_add_meal_entry_happy_path(add_meal_entry_handler: AddMealEntryCommandHandler, repo: AsyncMock):
    repo.get_profile.return_value = _valid_profile()
    repo.ensure_daily_diary.return_value = 99
    repo.add_meal_entry.return_value = 123

    out = await add_meal_entry_handler.handle(
        AddMealEntryCommand(
            user_id=1,
            food_id=10,
            meal_type="dinner",
            weight_grams=150.0,
            target_date=date(2026, 4, 7),
        )
    )

    assert out == 123
    repo.add_meal_entry.assert_awaited_once_with(diary_id=99, food_id=10, meal_type="dinner", weight_grams=150.0)
    add_meal_entry_handler._bus.publish.assert_awaited_once_with(
        MealEntryAddedEvent(
            user_id=1,
            diary_id=99,
            meal_entry_id=123,
            food_id=10,
            meal_type="dinner",
            weight_grams=150.0,
            target_date=date(2026, 4, 7),
        )
    )


@pytest.mark.asyncio
async def test_delete_meal_entry_not_found(delete_meal_entry_handler: DeleteMealEntryCommandHandler, repo: AsyncMock):
    repo.get_profile.return_value = _valid_profile()
    repo.get_user_meal_entry_target_date.return_value = None

    with pytest.raises(MealEntryNotFoundError) as exc:
        await delete_meal_entry_handler.handle(DeleteMealEntryCommand(user_id=1, meal_entry_id=404))
    assert "Meal entry" in exc.value.message


@pytest.mark.asyncio
async def test_delete_meal_entry_happy_path(delete_meal_entry_handler: DeleteMealEntryCommandHandler, repo: AsyncMock):
    repo.get_profile.return_value = _valid_profile()
    repo.get_user_meal_entry_target_date.return_value = date(2026, 4, 7)

    out = await delete_meal_entry_handler.handle(DeleteMealEntryCommand(user_id=1, meal_entry_id=404))

    assert out == 404
    delete_meal_entry_handler._bus.publish.assert_awaited_once_with(MealEntryDeletedEvent(user_id=1, meal_entry_id=404, target_date=date(2026, 4, 7)))


@pytest.mark.asyncio
async def test_update_daily_diary_happy_path(update_daily_diary_handler: UpdateDailyDiaryCommandHandler, repo: AsyncMock):
    repo.update_daily_diary.return_value = {"id": 77}

    out = await update_daily_diary_handler.handle(
        UpdateDailyDiaryCommand(
            user_id=1,
            target_date=date(2026, 4, 7),
            water_ml=500,
            notes="good day",
        )
    )

    assert out == 77
    update_daily_diary_handler._bus.publish.assert_awaited_once_with(
        DailyDiaryUpdatedEvent(
            user_id=1,
            diary_id=77,
            target_date=date(2026, 4, 7),
            water_ml=500,
            notes="good day",
        )
    )


@pytest.mark.asyncio
async def test_get_daily_norm_missing_fields(get_daily_norm_handler: GetDailyNormQueryHandler, read_repo: AsyncMock):
    read_repo.get_profile.return_value = NutritionProfileDomain(
        age=None,
        weight=80.0,
        height=None,
        gender=Gender.MALE,
        fitness_goal=None,
    )

    with pytest.raises(IncompleteNutritionProfileError) as exc:
        await get_daily_norm_handler.handle(GetDailyNormQuery(user_id=1))
    assert "Missing: age, height, fitness_goal" in exc.value.message


@pytest.mark.asyncio
async def test_get_daily_norm_profile_not_found(get_daily_norm_handler: GetDailyNormQueryHandler, read_repo: AsyncMock):
    read_repo.get_profile.return_value = None

    with pytest.raises(NutritionProfileNotFoundError):
        await get_daily_norm_handler.handle(GetDailyNormQuery(user_id=1))
