from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.core.exceptions import BadRequestError, NotFoundError
from src.models.user import FitnessGoal, Gender
from src.repositories.nutrition import NutritionRepository
from src.services.nutrition import NutritionService


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock(spec=NutritionRepository)


@pytest.fixture
def service(repo: AsyncMock) -> NutritionService:
    uow = AsyncMock()
    uow.repo = repo
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False
    return NutritionService(uow)


def _valid_profile():
    return SimpleNamespace(
        age=30,
        weight=80.0,
        height=180.0,
        gender=Gender.MALE,
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
    )


@pytest.mark.asyncio
async def test_get_day_overview_calculates_remaining_and_floors_zero(service: NutritionService, repo: AsyncMock):

    async def fake_get_daily_norm(_user_id: int):
        return {
            "calories": 2000.0,
            "protein_g": 150.0,
            "fat_g": 70.0,
            "carbs_g": 220.0,
        }

    service.get_daily_norm = fake_get_daily_norm

    repo.get_day_consumed_totals.return_value = {
        "calories": 2500.0,
        "protein_g": 180.0,
        "fat_g": 30.0,
        "carbs_g": 100.0,
    }

    out = await service.get_day_overview(1, date(2026, 4, 7))

    assert out["remaining"]["calories"] == 0.0
    assert out["remaining"]["protein_g"] == 0.0
    assert out["remaining"]["fat_g"] == 40.0
    assert out["remaining"]["carbs_g"] == 120.0


@pytest.mark.asyncio
async def test_add_meal_entry_rejects_non_positive_weight(service: NutritionService):

    with pytest.raises(BadRequestError) as exc:
        await service.add_meal_entry_and_recalculate(
            user_id=1,
            food_id=10,
            meal_type="lunch",
            weight_grams=0,
        )
    assert "greater than 0" in exc.value.message


@pytest.mark.asyncio
async def test_add_meal_entry_rejects_blank_meal_type(service: NutritionService):

    with pytest.raises(BadRequestError) as exc:
        await service.add_meal_entry_and_recalculate(
            user_id=1,
            food_id=10,
            meal_type="   ",
            weight_grams=120,
        )
    assert "Meal type is required" in exc.value.message


@pytest.mark.asyncio
async def test_add_meal_entry_happy_path(service: NutritionService, repo: AsyncMock):

    repo.get_user_profile.return_value = _valid_profile()
    repo.get_or_create_daily_diary.return_value = SimpleNamespace(id=99)
    repo.add_meal_entry.return_value = SimpleNamespace(id=123, meal_type="dinner")

    async def fake_get_day_overview(_user_id: int, _day: date):
        return {
            "remaining": {
                "calories": 1000.0,
                "protein_g": 80.0,
                "fat_g": 35.0,
                "carbs_g": 120.0,
            }
        }

    service.get_day_overview = fake_get_day_overview

    out = await service.add_meal_entry_and_recalculate(
        user_id=1,
        food_id=10,
        meal_type="dinner",
        weight_grams=150.0,
        target_date=date(2026, 4, 7),
    )

    assert out["meal_entry_id"] == 123
    assert out["target_date"] == date(2026, 4, 7)
    assert out["remaining"]["calories"] == 1000.0
    repo.add_meal_entry.assert_awaited_once_with(diary_id=99, food_id=10, meal_type="dinner", weight_grams=150.0)


@pytest.mark.asyncio
async def test_delete_meal_entry_not_found(service: NutritionService, repo: AsyncMock):

    repo.get_user_profile.return_value = _valid_profile()
    repo.get_user_meal_entry_with_target_date.return_value = None

    with pytest.raises(NotFoundError) as exc:
        await service.delete_meal_entry_and_recalculate(user_id=1, meal_entry_id=404)
    assert "Meal entry" in exc.value.message


@pytest.mark.asyncio
async def test_get_validated_profile_missing_fields(service: NutritionService, repo: AsyncMock):

    repo.get_user_profile.return_value = SimpleNamespace(
        age=None,
        weight=80.0,
        height=None,
        gender=Gender.MALE,
        fitness_goal=None,
    )

    with pytest.raises(BadRequestError) as exc:
        await service._get_validated_profile(1)
    assert "Missing: age, height, fitness_goal" in exc.value.message
