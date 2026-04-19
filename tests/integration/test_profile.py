import pytest
from httpx import AsyncClient


@pytest.fixture
async def fitness_payload():
    return {
        "weight": 75.0,
        "height": 180.0,
        "age": 25,
        "gender": "male",
        "fitness_goal": "muscle gain",
    }


@pytest.fixture
async def profile_with_fitness(client: AsyncClient, auth_headers: dict, fitness_payload: dict):
    await client.put("/profile/me/fitness", headers=auth_headers, json=fitness_payload)
    return fitness_payload


class TestGetProfile:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/profile/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_returns_correct_user_data(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == registered_user["email"]
        assert data["name"] == registered_user["name"]

    @pytest.mark.asyncio
    async def test_contains_required_fields(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/profile/me", headers=auth_headers)
        data = resp.json()
        for field in ("id", "email", "name", "is_verified", "is_2fa_enabled", "profile"):
            assert field in data, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_never_exposes_sensitive_fields(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/profile/me", headers=auth_headers)
        data = resp.json()
        assert "password_hash" not in data
        assert "totp_secret" not in data
        assert "oauth_provider_id" not in data

    @pytest.mark.asyncio
    async def test_fitness_initially_null_or_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/profile/me", headers=auth_headers)
        data = resp.json()
        profile = data.get("profile")
        if profile is not None:
            assert profile.get("weight") is None
            assert profile.get("height") is None


class TestUpdateUserInfo:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.patch("/profile/me", json={"name": "Hacker"})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_update_name_returns_200(self, client: AsyncClient, auth_headers: dict):
        resp = await client.patch("/profile/me", headers=auth_headers, json={"name": "Updated Name"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_name_persists(self, client: AsyncClient, auth_headers: dict):
        await client.patch("/profile/me", headers=auth_headers, json={"name": "Persisted Name"})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["name"] == "Persisted Name"

    @pytest.mark.asyncio
    async def test_update_avatar_url_returns_200(self, client: AsyncClient, auth_headers: dict):
        resp = await client.patch("/profile/me", headers=auth_headers, json={"avatar_url": "https://example.com/avatar.png"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_avatar_url_persists(self, client: AsyncClient, auth_headers: dict):
        url = "https://example.com/avatar.png"
        await client.patch("/profile/me", headers=auth_headers, json={"avatar_url": url})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["avatar_url"] == url

    @pytest.mark.asyncio
    async def test_update_both_fields_returns_200(self, client: AsyncClient, auth_headers: dict):
        resp = await client.patch(
            "/profile/me",
            headers=auth_headers,
            json={"name": "Full Update", "avatar_url": "https://example.com/pic.png"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_both_fields_persist(self, client: AsyncClient, auth_headers: dict):
        await client.patch(
            "/profile/me",
            headers=auth_headers,
            json={"name": "Full Update", "avatar_url": "https://example.com/pic.png"},
        )
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["name"] == "Full Update"
        assert resp.json()["avatar_url"] == "https://example.com/pic.png"

    @pytest.mark.asyncio
    async def test_empty_body_is_noop_returns_200(self, client: AsyncClient, auth_headers: dict):
        resp = await client.patch("/profile/me", headers=auth_headers, json={})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_empty_body_does_not_change_name(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        await client.patch("/profile/me", headers=auth_headers, json={})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["name"] == registered_user["name"]

    @pytest.mark.asyncio
    async def test_name_too_short_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.patch("/profile/me", headers=auth_headers, json={"name": "X"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_name_too_short_does_not_change_name(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        await client.patch("/profile/me", headers=auth_headers, json={"name": "X"})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["name"] == registered_user["name"]

    @pytest.mark.asyncio
    async def test_name_too_long_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.patch("/profile/me", headers=auth_headers, json={"name": "A" * 51})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_avatar_url_too_long_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.patch("/profile/me", headers=auth_headers, json={"avatar_url": "https://example.com/" + "a" * 490})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_sequential_updates_last_wins(self, client: AsyncClient, auth_headers: dict):
        await client.patch("/profile/me", headers=auth_headers, json={"name": "First Name"})
        await client.patch("/profile/me", headers=auth_headers, json={"name": "Second Name"})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["name"] == "Second Name"

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.patch(
            "/profile/me",
            headers={"Authorization": "Bearer bad.token"},
            json={"name": "Attacker"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_does_not_mutate_data(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        await client.patch(
            "/profile/me",
            headers={"Authorization": "Bearer bad.token"},
            json={"name": "Attacker"},
        )
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["name"] == registered_user["name"]


class TestFitnessProfile:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.put("/profile/me/fitness", json={"weight": 70.0})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_full_update_returns_200(self, client: AsyncClient, auth_headers: dict, fitness_payload: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json=fitness_payload)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_full_update_returns_correct_values(self, client: AsyncClient, auth_headers: dict, fitness_payload: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json=fitness_payload)
        data = resp.json()
        assert data["weight"] == fitness_payload["weight"]
        assert data["height"] == fitness_payload["height"]
        assert data["age"] == fitness_payload["age"]
        assert data["gender"] == fitness_payload["gender"]
        assert data["fitness_goal"] == fitness_payload["fitness_goal"]

    @pytest.mark.asyncio
    async def test_bmi_calculated_correctly(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": 70.0, "height": 175.0})
        assert resp.json()["bmi"] == 22.9

    @pytest.mark.asyncio
    async def test_bmi_none_without_height(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": 70.0})
        assert resp.json()["bmi"] is None

    @pytest.mark.asyncio
    async def test_bmi_none_without_weight(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"height": 175.0})
        assert resp.json()["bmi"] is None

    @pytest.mark.asyncio
    async def test_partial_update_weight_only(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": 80.0})
        assert resp.status_code == 200
        assert resp.json()["weight"] == 80.0

    @pytest.mark.asyncio
    async def test_creates_profile_on_first_call(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"age": 30})
        assert resp.status_code == 200
        assert resp.json()["age"] == 30

    @pytest.mark.asyncio
    async def test_fitness_data_visible_in_get_profile(self, client: AsyncClient, auth_headers: dict, profile_with_fitness: dict):
        resp = await client.get("/profile/me", headers=auth_headers)
        profile = resp.json()["profile"]
        assert profile is not None
        assert profile["weight"] == profile_with_fitness["weight"]
        assert profile["height"] == profile_with_fitness["height"]

    @pytest.mark.asyncio
    async def test_sequential_updates_last_wins(self, client: AsyncClient, auth_headers: dict):
        await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": 70.0})
        await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": 85.0})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["profile"]["weight"] == 85.0

    @pytest.mark.asyncio
    async def test_idempotent_same_payload(self, client: AsyncClient, auth_headers: dict):
        payload = {"weight": 77.0, "height": 177.0}
        r1 = await client.put("/profile/me/fitness", headers=auth_headers, json=payload)
        r2 = await client.put("/profile/me/fitness", headers=auth_headers, json=payload)
        assert r1.status_code == r2.status_code == 200
        assert r1.json()["weight"] == r2.json()["weight"]

    @pytest.mark.asyncio
    async def test_empty_body_is_valid(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_negative_weight_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": -5.0})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_weight_does_not_mutate_profile(self, client: AsyncClient, auth_headers: dict, profile_with_fitness: dict):
        await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": -5.0})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["profile"]["weight"] == profile_with_fitness["weight"]

    @pytest.mark.asyncio
    async def test_zero_weight_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": 0.0})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_zero_weight_does_not_mutate_profile(self, client: AsyncClient, auth_headers: dict, profile_with_fitness: dict):
        await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": 0.0})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["profile"]["weight"] == profile_with_fitness["weight"]

    @pytest.mark.asyncio
    async def test_weight_above_max_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"weight": 800.0})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_height_above_max_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"height": 350.0})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_height_above_max_does_not_mutate_profile(self, client: AsyncClient, auth_headers: dict, profile_with_fitness: dict):
        await client.put("/profile/me/fitness", headers=auth_headers, json={"height": 350.0})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["profile"]["height"] == profile_with_fitness["height"]

    @pytest.mark.asyncio
    async def test_age_above_max_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"age": 200})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_age_above_max_does_not_mutate_profile(self, client: AsyncClient, auth_headers: dict, profile_with_fitness: dict):
        await client.put("/profile/me/fitness", headers=auth_headers, json={"age": 200})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["profile"]["age"] == profile_with_fitness["age"]

    @pytest.mark.asyncio
    async def test_invalid_gender_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"gender": "attack_helicopter"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_gender_does_not_mutate_profile(self, client: AsyncClient, auth_headers: dict, profile_with_fitness: dict):
        await client.put("/profile/me/fitness", headers=auth_headers, json={"gender": "attack_helicopter"})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["profile"]["gender"] == profile_with_fitness["gender"]

    @pytest.mark.asyncio
    async def test_invalid_fitness_goal_returns_422(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put("/profile/me/fitness", headers=auth_headers, json={"fitness_goal": "fly to moon"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_fitness_goal_does_not_mutate_profile(self, client: AsyncClient, auth_headers: dict, profile_with_fitness: dict):
        await client.put("/profile/me/fitness", headers=auth_headers, json={"fitness_goal": "fly to moon"})
        resp = await client.get("/profile/me", headers=auth_headers)
        assert resp.json()["profile"]["fitness_goal"] == profile_with_fitness["fitness_goal"]

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.put(
            "/profile/me/fitness",
            headers={"Authorization": "Bearer bad.token"},
            json={"weight": 70.0},
        )
        assert resp.status_code == 401


class TestDeleteAccount:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.delete("/profile/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_returns_204_no_body(self, client: AsyncClient, auth_headers: dict):
        resp = await client.delete("/profile/me", headers=auth_headers)
        assert resp.status_code == 204
        assert resp.content == b""

    @pytest.mark.asyncio
    async def test_deleted_user_cannot_login(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        await client.delete("/profile/me", headers=auth_headers)
        resp = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_deleted_user_access_token_is_rejected(self, client: AsyncClient, auth_headers: dict):
        await client.delete("/profile/me", headers=auth_headers)
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code in (200, 403)

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.delete("/profile/me", headers={"Authorization": "Bearer bad.token"})
        assert resp.status_code == 401
