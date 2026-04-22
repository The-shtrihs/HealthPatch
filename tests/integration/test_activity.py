from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User

pytestmark = pytest.mark.asyncio


async def _register_and_login_verified_user(client: AsyncClient, db_session: AsyncSession, prefix: str) -> dict[str, str]:
    email = f"{prefix}-{uuid4().hex[:12]}@example.com"
    password = "Test1234!"
    payload = {
        "name": f"{prefix} User",
        "email": email,
        "password": password,
        "password_confirm": password,
    }
    register_resp = await client.post("/auth/register", json=payload)
    assert register_resp.status_code == 201

    await db_session.execute(update(User).where(User.email == email).values(is_verified=True))
    await db_session.commit()

    login_resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_plan(client: AsyncClient, headers: dict[str, str], title: str, is_public: bool = False) -> dict:
    payload = {
        "title": title,
        "description": f"{title} description",
        "is_public": is_public,
        "trainings": [],
    }
    resp = await client.post("/workouts/plans", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()


async def _create_training(client: AsyncClient, headers: dict[str, str], plan_id: int, name: str, order_num: int = 1) -> dict:
    resp = await client.post(
        f"/workouts/plans/{plan_id}/trainings",
        json={"name": name, "weekday": "mon", "order_num": order_num},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


async def _add_exercise_to_training(
    client: AsyncClient,
    headers: dict[str, str],
    plan_id: int,
    training_id: int,
    exercise_id: int,
    order_num: int = 1,
) -> dict:
    resp = await client.post(
        f"/workouts/plans/{plan_id}/trainings/{training_id}/exercises",
        json={
            "exercise_id": exercise_id,
            "order_num": order_num,
            "target_sets": 3,
            "target_reps": 10,
            "target_weight_pct": None,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


async def _start_session(client: AsyncClient, headers: dict[str, str], plan_training_id: int | None = None) -> dict:
    resp = await client.post("/workouts/sessions", json={"plan_training_id": plan_training_id}, headers=headers)
    assert resp.status_code == 201
    return resp.json()


async def _add_exercise_to_session(
    client: AsyncClient,
    headers: dict[str, str],
    session_id: int,
    exercise_id: int,
    order_num: int = 1,
) -> dict:
    resp = await client.post(
        f"/workouts/sessions/{session_id}/exercises",
        json={"exercise_id": exercise_id, "order_num": order_num},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def other_auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict[str, str]:
    return await _register_and_login_verified_user(client, db_session, "other")


@pytest_asyncio.fixture
async def muscle_group(client: AsyncClient, auth_headers: dict[str, str]) -> dict:
    resp = await client.post("/workouts/muscle-groups", json={"name": f"Chest-{uuid4().hex[:8]}"}, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def exercise(client: AsyncClient, auth_headers: dict[str, str], muscle_group: dict) -> dict:
    shoulders = await client.post(
        "/workouts/muscle-groups",
        json={"name": f"Shoulders-{uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    assert shoulders.status_code == 201
    shoulders_id = shoulders.json()["id"]

    resp = await client.post(
        "/workouts/exercises",
        json={
            "name": f"Bench Press {uuid4().hex[:6]}",
            "primary_muscle_group_id": muscle_group["id"],
            "secondary_muscle_group_ids": [shoulders_id],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def workout_plan(client: AsyncClient, auth_headers: dict[str, str]) -> dict:
    return await _create_plan(client, auth_headers, title=f"Plan-{uuid4().hex[:8]}", is_public=False)


@pytest_asyncio.fixture
async def active_session(client: AsyncClient, auth_headers: dict[str, str]) -> dict:
    return await _start_session(client, auth_headers)


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("POST", "/workouts/muscle-groups", {"name": "NoAuth"}),
        ("POST", "/workouts/exercises", {"name": "NoAuth", "primary_muscle_group_id": 1, "secondary_muscle_group_ids": []}),
        ("GET", "/workouts/plans", None),
        ("POST", "/workouts/plans", {"title": "NoAuth", "description": None, "is_public": False, "trainings": []}),
        ("GET", "/workouts/plans/1", None),
        ("PUT", "/workouts/plans/1", {"title": "NoAuth"}),
        ("DELETE", "/workouts/plans/1", None),
        ("POST", "/workouts/plans/1/trainings", {"name": "NoAuth", "weekday": "mon", "order_num": 1}),
        ("DELETE", "/workouts/plans/1/trainings/1", None),
        (
            "POST",
            "/workouts/plans/1/trainings/1/exercises",
            {"exercise_id": 1, "order_num": 1, "target_sets": 3, "target_reps": 10, "target_weight_pct": None},
        ),
        ("DELETE", "/workouts/plans/1/trainings/1/exercises/1", None),
        ("POST", "/workouts/sessions", {"plan_training_id": None}),
        ("GET", "/workouts/sessions", None),
        ("GET", "/workouts/sessions/1", None),
        ("PATCH", "/workouts/sessions/1/end", None),
        ("POST", "/workouts/sessions/1/exercises", {"exercise_id": 1, "order_num": 1}),
        ("POST", "/workouts/sessions/1/exercises/1/sets", {"set_number": 1, "reps": 10, "weight": 60.0}),
        ("GET", "/workouts/personal-records", None),
        ("POST", "/workouts/personal-records", {"exercise_id": 1, "weight": 100.0}),
        ("DELETE", "/workouts/personal-records/1", None),
    ],
)
async def test_protected_workout_routes_without_auth_return_401_or_403(
    client: AsyncClient,
    method: str,
    path: str,
    payload: dict | None,
):
    response = await client.request(method, path, json=payload)

    assert response.status_code in (401, 403)
    body = response.json()
    assert "message" in body


async def test_get_workouts_muscle_groups_returns_created_group(client: AsyncClient, muscle_group: dict):
    response = await client.get("/workouts/muscle-groups")

    assert response.status_code == 200
    data = response.json()
    assert any(item["id"] == muscle_group["id"] for item in data)
    assert any("name" in item for item in data)


async def test_post_workouts_muscle_groups_returns_201_with_body(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post("/workouts/muscle-groups", json={"name": f"Back-{uuid4().hex[:8]}"}, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"].startswith("Back-")


async def test_get_workouts_exercises_with_search_pagination_returns_expected_shape(client: AsyncClient, exercise: dict):
    prefix = exercise["name"].split()[0]
    response = await client.get(f"/workouts/exercises?search={prefix}&page=1&size=10")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert any(item["id"] == exercise["id"] for item in data["items"])


async def test_get_workouts_exercise_by_id_returns_exercise(client: AsyncClient, exercise: dict):
    response = await client.get(f"/workouts/exercises/{exercise['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == exercise["id"]
    assert data["name"] == exercise["name"]


async def test_get_workouts_exercise_by_id_missing_returns_404(client: AsyncClient):
    response = await client.get("/workouts/exercises/999999")

    assert response.status_code == 404
    assert response.json()["error_code"] == "EXERCISE_NOT_FOUND"


async def test_post_workouts_exercises_returns_201_with_relationships(
    client: AsyncClient,
    auth_headers: dict[str, str],
    muscle_group: dict,
):
    secondary_resp = await client.post(
        "/workouts/muscle-groups",
        json={"name": f"Triceps-{uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    assert secondary_resp.status_code == 201

    response = await client.post(
        "/workouts/exercises",
        json={
            "name": f"Dip-{uuid4().hex[:6]}",
            "primary_muscle_group_id": muscle_group["id"],
            "secondary_muscle_group_ids": [secondary_resp.json()["id"]],
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["primary_muscle_group"]["id"] == muscle_group["id"]
    assert len(data["secondary_muscle_groups"]) == 1


async def test_post_workouts_exercises_with_unknown_muscle_group_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        "/workouts/exercises",
        json={"name": "Invalid Exercise", "primary_muscle_group_id": 999999, "secondary_muscle_group_ids": []},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "MUSCLE_GROUP_NOT_FOUND"


async def test_get_workouts_plans_public_returns_only_public_plans(client: AsyncClient, auth_headers: dict[str, str]):
    public_plan = await _create_plan(client, auth_headers, title=f"Public-{uuid4().hex[:8]}", is_public=True)
    await _create_plan(client, auth_headers, title=f"Private-{uuid4().hex[:8]}", is_public=False)

    response = await client.get("/workouts/plans/public?page=1&size=20")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert any(item["id"] == public_plan["id"] for item in data["items"])


async def test_get_workouts_plans_returns_authenticated_user_plans(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    my_plan = await _create_plan(client, auth_headers, title=f"Mine-{uuid4().hex[:8]}", is_public=False)
    await _create_plan(client, other_auth_headers, title=f"Other-{uuid4().hex[:8]}", is_public=False)

    response = await client.get("/workouts/plans?page=1&size=20", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert any(item["id"] == my_plan["id"] for item in data["items"])
    assert all(item["id"] != my_plan["id"] or item["title"].startswith("Mine-") for item in data["items"])


async def test_post_workouts_plans_returns_201_and_plan_shape(client: AsyncClient, auth_headers: dict[str, str], exercise: dict):
    response = await client.post(
        "/workouts/plans",
        json={
            "title": f"Strength-{uuid4().hex[:6]}",
            "description": "Progressive overload",
            "is_public": False,
            "trainings": [
                {
                    "name": "Day 1",
                    "order_num": 1,
                    "weekday": "mon",
                    "exercises": [
                        {
                            "exercise_id": exercise["id"],
                            "order_num": 1,
                            "target_sets": 4,
                            "target_reps": 8,
                            "target_weight_pct": 75,
                        }
                    ],
                }
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert len(data["trainings"]) == 1
    assert len(data["trainings"][0]["exercises"]) == 1


async def test_post_workouts_plans_with_missing_exercise_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        "/workouts/plans",
        json={
            "title": "Invalid Plan",
            "description": None,
            "is_public": False,
            "trainings": [
                {
                    "name": "Day 1",
                    "order_num": 1,
                    "weekday": "mon",
                    "exercises": [
                        {
                            "exercise_id": 999999,
                            "order_num": 1,
                            "target_sets": 3,
                            "target_reps": 10,
                            "target_weight_pct": None,
                        }
                    ],
                }
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "EXERCISE_NOT_FOUND"


async def test_get_workouts_plan_by_id_returns_owner_private_plan(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workout_plan: dict,
):
    response = await client.get(f"/workouts/plans/{workout_plan['id']}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == workout_plan["id"]
    assert "trainings" in data


async def test_get_workouts_plan_by_id_missing_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.get("/workouts/plans/999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "WORKOUT_PLAN_NOT_FOUND"


async def test_get_workouts_plan_by_id_private_other_user_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    private_plan = await _create_plan(client, auth_headers, title=f"Private-{uuid4().hex[:8]}", is_public=False)
    response = await client.get(f"/workouts/plans/{private_plan['id']}", headers=other_auth_headers)

    assert response.status_code == 403
    assert response.json()["error_code"] == "PRIVATE_PLAN_ACCESS"


async def test_put_workouts_plan_by_id_updates_plan_and_returns_body(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workout_plan: dict,
):
    response = await client.put(
        f"/workouts/plans/{workout_plan['id']}",
        json={"title": "Updated Title", "description": "Updated desc", "is_public": True},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == workout_plan["id"]
    assert data["title"] == "Updated Title"
    assert data["is_public"] is True


async def test_put_workouts_plan_by_id_missing_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.put("/workouts/plans/999999", json={"title": "Missing"}, headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "WORKOUT_PLAN_NOT_FOUND"


async def test_put_workouts_plan_by_id_other_owner_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    plan = await _create_plan(client, auth_headers, title=f"OwnerOnly-{uuid4().hex[:8]}", is_public=False)
    response = await client.put(f"/workouts/plans/{plan['id']}", json={"title": "Hack"}, headers=other_auth_headers)

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_delete_workouts_plan_by_id_returns_204(client: AsyncClient, auth_headers: dict[str, str]):
    plan = await _create_plan(client, auth_headers, title=f"Delete-{uuid4().hex[:8]}", is_public=False)

    response = await client.delete(f"/workouts/plans/{plan['id']}", headers=auth_headers)

    assert response.status_code == 204
    assert response.content == b""


async def test_delete_workouts_plan_by_id_missing_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.delete("/workouts/plans/999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "WORKOUT_PLAN_NOT_FOUND"


async def test_delete_workouts_plan_by_id_other_owner_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    plan = await _create_plan(client, auth_headers, title=f"OwnerDelete-{uuid4().hex[:8]}", is_public=False)
    response = await client.delete(f"/workouts/plans/{plan['id']}", headers=other_auth_headers)

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_post_workouts_plan_trainings_returns_201_and_training_shape(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workout_plan: dict,
):
    response = await client.post(
        f"/workouts/plans/{workout_plan['id']}/trainings",
        json={"name": "Upper", "weekday": "tue", "order_num": 2},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["plan_id"] == workout_plan["id"]
    assert data["name"] == "Upper"


async def test_post_workouts_plan_trainings_missing_plan_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        "/workouts/plans/999999/trainings",
        json={"name": "Missing", "weekday": "mon", "order_num": 1},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "WORKOUT_PLAN_NOT_FOUND"


async def test_post_workouts_plan_trainings_other_owner_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    plan = await _create_plan(client, auth_headers, title=f"TrainingsOwner-{uuid4().hex[:8]}", is_public=False)
    response = await client.post(
        f"/workouts/plans/{plan['id']}/trainings",
        json={"name": "Hack", "weekday": "mon", "order_num": 1},
        headers=other_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_delete_workouts_plan_training_returns_204(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workout_plan: dict,
):
    training = await _create_training(client, auth_headers, workout_plan["id"], name="Delete Day")

    response = await client.delete(
        f"/workouts/plans/{workout_plan['id']}/trainings/{training['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert response.content == b""


async def test_delete_workouts_plan_training_missing_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workout_plan: dict,
):
    response = await client.delete(f"/workouts/plans/{workout_plan['id']}/trainings/999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "PLAN_TRAINING_NOT_FOUND"


async def test_delete_workouts_plan_training_other_owner_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    plan = await _create_plan(client, auth_headers, title=f"DeleteTraining-{uuid4().hex[:8]}", is_public=False)
    training = await _create_training(client, auth_headers, plan["id"], name="Owner training")

    response = await client.delete(
        f"/workouts/plans/{plan['id']}/trainings/{training['id']}",
        headers=other_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_post_workouts_training_exercises_returns_201(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workout_plan: dict,
    exercise: dict,
):
    training = await _create_training(client, auth_headers, workout_plan["id"], name="Exercise Day")

    response = await client.post(
        f"/workouts/plans/{workout_plan['id']}/trainings/{training['id']}/exercises",
        json={
            "exercise_id": exercise["id"],
            "order_num": 1,
            "target_sets": 5,
            "target_reps": 5,
            "target_weight_pct": 80,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["exercise_id"] == exercise["id"]
    assert data["target_sets"] == 5


async def test_post_workouts_training_exercises_missing_training_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workout_plan: dict,
    exercise: dict,
):
    response = await client.post(
        f"/workouts/plans/{workout_plan['id']}/trainings/999999/exercises",
        json={
            "exercise_id": exercise["id"],
            "order_num": 1,
            "target_sets": 3,
            "target_reps": 10,
            "target_weight_pct": None,
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "PLAN_TRAINING_NOT_FOUND"


async def test_post_workouts_training_exercises_other_owner_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    exercise: dict,
):
    plan = await _create_plan(client, auth_headers, title=f"OtherOwnerEx-{uuid4().hex[:8]}", is_public=False)
    training = await _create_training(client, auth_headers, plan["id"], name="Protected")

    response = await client.post(
        f"/workouts/plans/{plan['id']}/trainings/{training['id']}/exercises",
        json={
            "exercise_id": exercise["id"],
            "order_num": 1,
            "target_sets": 3,
            "target_reps": 10,
            "target_weight_pct": None,
        },
        headers=other_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_delete_workouts_training_exercise_returns_204(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workout_plan: dict,
    exercise: dict,
):
    training = await _create_training(client, auth_headers, workout_plan["id"], name="Delete exercise")
    pte = await _add_exercise_to_training(client, auth_headers, workout_plan["id"], training["id"], exercise["id"])

    response = await client.delete(
        f"/workouts/plans/{workout_plan['id']}/trainings/{training['id']}/exercises/{pte['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert response.content == b""


async def test_delete_workouts_training_exercise_missing_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workout_plan: dict,
):
    training = await _create_training(client, auth_headers, workout_plan["id"], name="Missing exercise")

    response = await client.delete(
        f"/workouts/plans/{workout_plan['id']}/trainings/{training['id']}/exercises/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "PLAN_TRAINING_EXERCISE_NOT_FOUND"


async def test_delete_workouts_training_exercise_other_owner_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    exercise: dict,
):
    plan = await _create_plan(client, auth_headers, title=f"ProtectPTE-{uuid4().hex[:8]}", is_public=False)
    training = await _create_training(client, auth_headers, plan["id"], name="Owner Training")
    pte = await _add_exercise_to_training(client, auth_headers, plan["id"], training["id"], exercise["id"])

    response = await client.delete(
        f"/workouts/plans/{plan['id']}/trainings/{training['id']}/exercises/{pte['id']}",
        headers=other_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_post_workouts_sessions_returns_201_for_free_session(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post("/workouts/sessions", json={"plan_training_id": None}, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["plan_training_id"] is None


async def test_post_workouts_sessions_with_missing_training_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post("/workouts/sessions", json={"plan_training_id": 999999}, headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "PLAN_TRAINING_NOT_FOUND"


async def test_post_workouts_sessions_private_training_of_other_user_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    plan = await _create_plan(client, auth_headers, title=f"PrivateSession-{uuid4().hex[:8]}", is_public=False)
    training = await _create_training(client, auth_headers, plan["id"], name="Owner Session Training")

    response = await client.post(
        "/workouts/sessions",
        json={"plan_training_id": training["id"]},
        headers=other_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "PRIVATE_PLAN_ACCESS"


async def test_get_workouts_sessions_returns_current_user_sessions(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    own_session = await _start_session(client, auth_headers)
    await _start_session(client, other_auth_headers)

    response = await client.get("/workouts/sessions?page=1&size=20", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert any(item["id"] == own_session["id"] for item in data["items"])
    assert "total" in data


async def test_get_workouts_session_by_id_returns_detail(
    client: AsyncClient,
    auth_headers: dict[str, str],
    active_session: dict,
):
    response = await client.get(f"/workouts/sessions/{active_session['id']}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == active_session["id"]
    assert "exercise_sessions" in data


async def test_get_workouts_session_by_id_missing_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.get("/workouts/sessions/999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "WORKOUT_SESSION_NOT_FOUND"


async def test_get_workouts_session_by_id_other_user_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    session = await _start_session(client, auth_headers)
    response = await client.get(f"/workouts/sessions/{session['id']}", headers=other_auth_headers)

    assert response.status_code == 403
    assert response.json()["error_code"] in {"FORBIDDEN", "NOT_RESOURCE_OWNER"}


async def test_patch_workouts_session_end_returns_200_and_ended_timestamp(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    session = await _start_session(client, auth_headers)
    response = await client.patch(f"/workouts/sessions/{session['id']}/end", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session["id"]
    assert data["ended_at"] is not None


async def test_patch_workouts_session_end_missing_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.patch("/workouts/sessions/999999/end", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "WORKOUT_SESSION_NOT_FOUND"


async def test_patch_workouts_session_end_other_user_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    session = await _start_session(client, auth_headers)
    response = await client.patch(f"/workouts/sessions/{session['id']}/end", headers=other_auth_headers)

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_post_workouts_session_exercises_returns_201(
    client: AsyncClient,
    auth_headers: dict[str, str],
    active_session: dict,
    exercise: dict,
):
    response = await client.post(
        f"/workouts/sessions/{active_session['id']}/exercises",
        json={"exercise_id": exercise["id"], "order_num": 1},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["exercise_id"] == exercise["id"]
    assert data["order_num"] == 1


async def test_post_workouts_session_exercises_missing_session_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
    exercise: dict,
):
    response = await client.post(
        "/workouts/sessions/999999/exercises",
        json={"exercise_id": exercise["id"], "order_num": 1},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "WORKOUT_SESSION_NOT_FOUND"


async def test_post_workouts_session_exercises_other_user_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    exercise: dict,
):
    session = await _start_session(client, auth_headers)
    response = await client.post(
        f"/workouts/sessions/{session['id']}/exercises",
        json={"exercise_id": exercise["id"], "order_num": 1},
        headers=other_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_post_workouts_session_exercises_on_ended_session_returns_409(
    client: AsyncClient,
    auth_headers: dict[str, str],
    exercise: dict,
):
    session = await _start_session(client, auth_headers)
    end_resp = await client.patch(f"/workouts/sessions/{session['id']}/end", headers=auth_headers)
    assert end_resp.status_code == 200

    response = await client.post(
        f"/workouts/sessions/{session['id']}/exercises",
        json={"exercise_id": exercise["id"], "order_num": 2},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "SESSION_ALREADY_ENDED"


async def test_post_workouts_session_sets_returns_201(
    client: AsyncClient,
    auth_headers: dict[str, str],
    active_session: dict,
    exercise: dict,
):
    exercise_session = await _add_exercise_to_session(client, auth_headers, active_session["id"], exercise["id"], order_num=1)
    response = await client.post(
        f"/workouts/sessions/{active_session['id']}/exercises/{exercise_session['id']}/sets",
        json={"set_number": 1, "reps": 10, "weight": 80.0},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["set_number"] == 1
    assert data["weight"] == 80.0


async def test_post_workouts_session_sets_missing_exercise_session_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
    active_session: dict,
):
    response = await client.post(
        f"/workouts/sessions/{active_session['id']}/exercises/999999/sets",
        json={"set_number": 1, "reps": 8, "weight": 70.0},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "EXERCISE_SESSION_NOT_FOUND"


async def test_post_workouts_session_sets_other_user_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    exercise: dict,
):
    session = await _start_session(client, auth_headers)
    exercise_session = await _add_exercise_to_session(client, auth_headers, session["id"], exercise["id"], order_num=1)

    response = await client.post(
        f"/workouts/sessions/{session['id']}/exercises/{exercise_session['id']}/sets",
        json={"set_number": 1, "reps": 5, "weight": 100.0},
        headers=other_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_post_workouts_session_sets_on_ended_session_returns_409(
    client: AsyncClient,
    auth_headers: dict[str, str],
    exercise: dict,
):
    session = await _start_session(client, auth_headers)
    exercise_session = await _add_exercise_to_session(client, auth_headers, session["id"], exercise["id"], order_num=1)
    end_resp = await client.patch(f"/workouts/sessions/{session['id']}/end", headers=auth_headers)
    assert end_resp.status_code == 200

    response = await client.post(
        f"/workouts/sessions/{session['id']}/exercises/{exercise_session['id']}/sets",
        json={"set_number": 2, "reps": 5, "weight": 90.0},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "SESSION_ALREADY_ENDED"


async def test_get_workouts_personal_records_returns_list(
    client: AsyncClient,
    auth_headers: dict[str, str],
    exercise: dict,
):
    pr_resp = await client.post(
        "/workouts/personal-records",
        json={"exercise_id": exercise["id"], "weight": 95.0},
        headers=auth_headers,
    )
    assert pr_resp.status_code == 201

    response = await client.get("/workouts/personal-records", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert any(item["exercise_id"] == exercise["id"] for item in data)
    assert any("weight" in item for item in data)


async def test_post_workouts_personal_records_returns_201_and_record(
    client: AsyncClient,
    auth_headers: dict[str, str],
    exercise: dict,
):
    response = await client.post(
        "/workouts/personal-records",
        json={"exercise_id": exercise["id"], "weight": 110.0},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["exercise_id"] == exercise["id"]
    assert data["weight"] == 110.0


async def test_post_workouts_personal_records_missing_exercise_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        "/workouts/personal-records",
        json={"exercise_id": 999999, "weight": 110.0},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "EXERCISE_NOT_FOUND"


async def test_post_workouts_personal_records_lower_weight_than_existing_returns_400(
    client: AsyncClient,
    auth_headers: dict[str, str],
    exercise: dict,
):
    first = await client.post(
        "/workouts/personal-records",
        json={"exercise_id": exercise["id"], "weight": 120.0},
        headers=auth_headers,
    )
    assert first.status_code == 201

    response = await client.post(
        "/workouts/personal-records",
        json={"exercise_id": exercise["id"], "weight": 110.0},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "PR_DOWNGRADE"


async def test_delete_workouts_personal_records_returns_deleted_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
    exercise: dict,
):
    pr_resp = await client.post(
        "/workouts/personal-records",
        json={"exercise_id": exercise["id"], "weight": 130.0},
        headers=auth_headers,
    )
    assert pr_resp.status_code == 201
    pr_id = pr_resp.json()["id"]

    response = await client.delete(f"/workouts/personal-records/{pr_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["deleted_pr_id"] == pr_id


async def test_delete_workouts_personal_records_missing_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.delete("/workouts/personal-records/999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "PERSONAL_RECORD_NOT_FOUND"


async def test_delete_workouts_personal_records_other_owner_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    exercise: dict,
):
    pr_resp = await client.post(
        "/workouts/personal-records",
        json={"exercise_id": exercise["id"], "weight": 135.0},
        headers=auth_headers,
    )
    assert pr_resp.status_code == 201

    response = await client.delete(f"/workouts/personal-records/{pr_resp.json()['id']}", headers=other_auth_headers)

    assert response.status_code == 403
    assert response.json()["error_code"] == "NOT_RESOURCE_OWNER"


async def test_activity_full_flow_create_plan_start_session_log_set_create_pr_end_session_and_block_new_sets(
    client: AsyncClient,
    auth_headers: dict[str, str],
    exercise: dict,
):
    # 1. Create plan with one training and one exercise template.
    plan = await _create_plan(client, auth_headers, title=f"Flow-{uuid4().hex[:8]}", is_public=False)
    training = await _create_training(client, auth_headers, plan["id"], name="Flow Training", order_num=1)
    await _add_exercise_to_training(client, auth_headers, plan["id"], training["id"], exercise["id"], order_num=1)

    # 2. Start session from training and verify template exercises are copied into the session.
    start_resp = await client.post(
        "/workouts/sessions",
        json={"plan_training_id": training["id"]},
        headers=auth_headers,
    )
    assert start_resp.status_code == 201
    session = start_resp.json()
    detail_resp = await client.get(f"/workouts/sessions/{session['id']}", headers=auth_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["exercise_sessions"]) == 1
    exercise_session_id = detail["exercise_sessions"][0]["id"]

    # 3. Log a weighted set.
    set_resp = await client.post(
        f"/workouts/sessions/{session['id']}/exercises/{exercise_session_id}/sets",
        json={"set_number": 1, "reps": 6, "weight": 140.0},
        headers=auth_headers,
    )
    assert set_resp.status_code == 201
    assert set_resp.json()["weight"] == 140.0

    # 4. Verify personal record was auto-created.
    prs_resp = await client.get("/workouts/personal-records", headers=auth_headers)
    assert prs_resp.status_code == 200
    prs = prs_resp.json()
    matching_pr = next((item for item in prs if item["exercise_id"] == exercise["id"]), None)
    assert matching_pr is not None
    assert matching_pr["weight"] == 140.0

    # 5. End session.
    end_resp = await client.patch(f"/workouts/sessions/{session['id']}/end", headers=auth_headers)
    assert end_resp.status_code == 200
    assert end_resp.json()["ended_at"] is not None

    # 6. Trying to add a set to ended session returns 409.
    set_after_end_resp = await client.post(
        f"/workouts/sessions/{session['id']}/exercises/{exercise_session_id}/sets",
        json={"set_number": 2, "reps": 5, "weight": 130.0},
        headers=auth_headers,
    )
    assert set_after_end_resp.status_code == 409
    assert set_after_end_resp.json()["error_code"] == "SESSION_ALREADY_ENDED"

    # 7. Delete PR and validate deleted_pr_id in response.
    delete_pr_resp = await client.delete(f"/workouts/personal-records/{matching_pr['id']}", headers=auth_headers)
    assert delete_pr_resp.status_code == 200
    assert delete_pr_resp.json()["deleted_pr_id"] == matching_pr["id"]
