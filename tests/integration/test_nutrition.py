import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.nutrition import Food
from src.models.user import FitnessGoal, Gender, User, UserProfile


async def _get_test_user(db_session: AsyncSession) -> User:
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    return result.scalar_one()


async def _seed_complete_profile(db_session: AsyncSession) -> User:
    user = await _get_test_user(db_session)
    profile = UserProfile(
        user_id=user.id,
        age=30,
        weight=80.0,
        height=180.0,
        gender=Gender.MALE,
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
    )
    db_session.add(profile)
    await db_session.commit()
    return user


async def _seed_food(db_session: AsyncSession, fdc_id: int) -> Food:
    food = Food(
        fdc_id=fdc_id,
        name="Test Oats",
        brand_name="TestBrand",
        data_type="Branded",
        calories_per_100g=380.0,
        protein_per_100g=13.0,
        carbs_per_100g=67.0,
        fat_per_100g=7.0,
        is_verified=True,
    )
    db_session.add(food)
    await db_session.commit()
    await db_session.refresh(food)
    return food


@pytest.mark.asyncio
async def test_get_daily_norm_requires_profile(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/nutrition/norm", headers=auth_headers)

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == "NOT_FOUND"
    assert "Nutrition profile" in body["message"]


@pytest.mark.asyncio
async def test_get_daily_norm_success(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    await _seed_complete_profile(db_session)

    resp = await client.get("/nutrition/norm", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["calories"] > 0
    assert body["protein_g"] > 0
    assert body["fat_g"] > 0
    assert body["carbs_g"] >= 0


@pytest.mark.asyncio
async def test_add_meal_entry_and_overview_success(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    await _seed_complete_profile(db_session)
    food = await _seed_food(db_session, fdc_id=900001)

    add_resp = await client.post(
        "/nutrition/entries",
        headers=auth_headers,
        json={
            "food_id": food.id,
            "meal_type": "breakfast",
            "weight_grams": 50.0,
            "target_date": "2026-04-07",
        },
    )

    assert add_resp.status_code == 201
    add_body = add_resp.json()
    assert add_body["meal_entry_id"] > 0
    assert add_body["target_date"] == "2026-04-07"
    assert add_body["remaining"]["calories"] >= 0

    overview_resp = await client.get(
        "/nutrition/overview",
        headers=auth_headers,
        params={"target_date": "2026-04-07"},
    )

    assert overview_resp.status_code == 200
    overview = overview_resp.json()
    assert overview["target_date"] == "2026-04-07"
    assert overview["consumed"]["calories"] > 0
    assert overview["consumed"]["protein_g"] > 0


@pytest.mark.asyncio
async def test_add_meal_entry_validation_error(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/nutrition/entries",
        headers=auth_headers,
        json={
            "food_id": 1,
            "meal_type": "lunch",
            "weight_grams": 0,
            "target_date": "2026-04-07",
        },
    )

    assert resp.status_code == 422
    body = resp.json()
    assert body["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_delete_meal_entry_not_found(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    await _seed_complete_profile(db_session)

    resp = await client.delete("/nutrition/entries/999999", headers=auth_headers)

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == "NOT_FOUND"
    assert "Meal entry" in body["message"]


@pytest.mark.asyncio
async def test_delete_meal_entry_success(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    await _seed_complete_profile(db_session)
    food = await _seed_food(db_session, fdc_id=900002)

    add_resp = await client.post(
        "/nutrition/entries",
        headers=auth_headers,
        json={
            "food_id": food.id,
            "meal_type": "dinner",
            "weight_grams": 120.0,
            "target_date": "2026-04-07",
        },
    )
    meal_entry_id = add_resp.json()["meal_entry_id"]

    del_resp = await client.delete(f"/nutrition/entries/{meal_entry_id}", headers=auth_headers)

    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["deleted_meal_entry_id"] == meal_entry_id
    assert body["target_date"] == "2026-04-07"


@pytest.mark.asyncio
async def test_update_daily_diary_success(client: AsyncClient, auth_headers: dict):
    resp = await client.patch(
        "/nutrition/diary",
        headers=auth_headers,
        json={
            "target_date": "2026-04-07",
            "water_ml": 2200,
            "notes": "Good hydration day",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["target_date"] == "2026-04-07"
    assert body["water_ml"] == 2200
    assert body["notes"] == "Good hydration day"
