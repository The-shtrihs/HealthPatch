from contextlib import asynccontextmanager
from datetime import date
from types import SimpleNamespace

import pytest

from src.core.exceptions import BadRequestError, NotFoundError
from src.models.user import FitnessGoal, Gender
from src.services.nutrition import NutritionService


class DummyDB:
    @asynccontextmanager
    async def begin(self):
        yield


class FakeNutritionRepo:
    def __init__(self):
        self.profile = None
        self.day_consumed_totals = {
            "calories": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "carbs_g": 0.0,
        }
        self.diary = SimpleNamespace(id=1)
        self.meal_entry = SimpleNamespace(id=1)
        self.meal_entry_row = None
        self.deleted_entry = None
        self.updated_diary = SimpleNamespace(
            id=1,
            user_id=1,
            target_date=date(2026, 4, 7),
            water_ml=0,
            notes=None,
        )

    async def get_user_profile(self, user_id: int):
        return self.profile

    async def get_day_consumed_totals(self, user_id: int, target_date: date):
        return self.day_consumed_totals

    async def get_or_create_daily_diary(self, user_id: int, target_date: date):
        return self.diary

    async def add_meal_entry(self, diary_id: int, food_id: int, meal_type: str, weight_grams: float):
        self.meal_entry = SimpleNamespace(
            id=self.meal_entry.id,
            diary_id=diary_id,
            food_id=food_id,
            meal_type=meal_type,
            weight_grams=weight_grams,
        )
        return self.meal_entry

    async def get_user_meal_entry_with_target_date(self, user_id: int, meal_entry_id: int):
        return self.meal_entry_row

    async def delete_meal_entry(self, meal_entry):
        self.deleted_entry = meal_entry

    async def update_daily_diary(self, user_id: int, target_date: date, water_ml: int | None, notes: str | None):
        self.updated_diary = SimpleNamespace(
            id=1,
            user_id=user_id,
            target_date=target_date,
            water_ml=0 if water_ml is None else water_ml,
            notes=notes,
        )
        return self.updated_diary


def _valid_profile():
    return SimpleNamespace(
        age=30,
        weight=80.0,
        height=180.0,
        gender=Gender.MALE,
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
    )


@pytest.mark.asyncio
async def test_get_day_overview_calculates_remaining_and_floors_zero():
    service = NutritionService(DummyDB())
    repo = FakeNutritionRepo()
    service.repo = repo

    async def fake_get_daily_norm(_user_id: int):
        return {
            "calories": 2000.0,
            "protein_g": 150.0,
            "fat_g": 70.0,
            "carbs_g": 220.0,
        }

    service.get_daily_norm = fake_get_daily_norm

    repo.day_consumed_totals = {
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
async def test_add_meal_entry_rejects_non_positive_weight():
    service = NutritionService(DummyDB())
    service.repo = FakeNutritionRepo()

    with pytest.raises(BadRequestError) as exc:
        await service.add_meal_entry_and_recalculate(
            user_id=1,
            food_id=10,
            meal_type="lunch",
            weight_grams=0,
        )
    assert "greater than 0" in exc.value.message


@pytest.mark.asyncio
async def test_add_meal_entry_rejects_blank_meal_type():
    service = NutritionService(DummyDB())
    service.repo = FakeNutritionRepo()

    with pytest.raises(BadRequestError) as exc:
        await service.add_meal_entry_and_recalculate(
            user_id=1,
            food_id=10,
            meal_type="   ",
            weight_grams=120,
        )
    assert "Meal type is required" in exc.value.message


@pytest.mark.asyncio
async def test_add_meal_entry_happy_path():
    service = NutritionService(DummyDB())
    repo = FakeNutritionRepo()
    service.repo = repo

    repo.profile = _valid_profile()
    repo.diary = SimpleNamespace(id=99)
    repo.meal_entry = SimpleNamespace(id=123)

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
    assert repo.meal_entry.meal_type == "dinner"


@pytest.mark.asyncio
async def test_delete_meal_entry_not_found():
    service = NutritionService(DummyDB())
    repo = FakeNutritionRepo()
    service.repo = repo

    repo.profile = _valid_profile()
    repo.meal_entry_row = None

    with pytest.raises(NotFoundError) as exc:
        await service.delete_meal_entry_and_recalculate(user_id=1, meal_entry_id=404)
    assert "Meal entry" in exc.value.message


@pytest.mark.asyncio
async def test_get_validated_profile_missing_fields():
    service = NutritionService(DummyDB())
    repo = FakeNutritionRepo()
    service.repo = repo

    repo.profile = SimpleNamespace(
        age=None,
        weight=80.0,
        height=None,
        gender=Gender.MALE,
        fitness_goal=None,
    )

    with pytest.raises(BadRequestError) as exc:
        await service._get_validated_profile(1)
    assert "Missing: age, height, fitness_goal" in exc.value.message
