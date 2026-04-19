import pytest
from httpx import AsyncClient


@pytest.fixture
def register_payload():
    return {
        "name": "Test User",
        "email": "integration_auth@example.com",
        "password": "Test1234!",
        "password_confirm": "Test1234!",
    }


@pytest.fixture
async def verified_auth_headers(client: AsyncClient, register_payload: dict) -> dict:
    await client.post("/auth/register", json=register_payload)
    return {}


class TestRegister:
    @pytest.mark.asyncio
    async def test_returns_201_on_success(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"name": "Fresh User", "email": "fresh_reg@example.com", "password": "Test1234!", "password_confirm": "Test1234!"},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_response_has_message(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"name": "Fresh User", "email": "fresh_reg2@example.com", "password": "Test1234!", "password_confirm": "Test1234!"},
        )
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/auth/register",
            json={"name": "Other", "email": registered_user["email"], "password": "Test1234!", "password_confirm": "Test1234!"},
        )
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "EMAIL_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_passwords_mismatch_returns_422(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"name": "User", "email": "mm@example.com", "password": "Test1234!", "password_confirm": "Different1!"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_weak_password_no_uppercase_returns_422(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"name": "User", "email": "weak@example.com", "password": "nouppercase1!", "password_confirm": "nouppercase1!"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_weak_password_no_special_char_returns_422(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"name": "User", "email": "weak2@example.com", "password": "NoSpecial123", "password_confirm": "NoSpecial123"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_weak_password_no_digit_returns_422(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"name": "User", "email": "weak3@example.com", "password": "NoDigitPass!", "password_confirm": "NoDigitPass!"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_name_too_short_returns_422(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"name": "X", "email": "short@example.com", "password": "Test1234!", "password_confirm": "Test1234!"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_email_format_returns_422(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"name": "User", "email": "not-an-email", "password": "Test1234!", "password_confirm": "Test1234!"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_required_fields_returns_422(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={"name": "User"})
        assert resp.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_verified_user_gets_tokens(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        resp = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": "WrongPass123!"},
        )
        assert resp.status_code == 401
        assert resp.json()["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_nonexistent_email_returns_401(self, client: AsyncClient):
        resp = await client.post("/auth/login", json={"email": "nobody@example.com", "password": "Test1234!"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_password_does_not_return_tokens(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": "WrongPass123!"},
        )
        assert "access_token" not in resp.json()

    @pytest.mark.asyncio
    async def test_invalid_email_format_returns_422(self, client: AsyncClient):
        resp = await client.post("/auth/login", json={"email": "not-email", "password": "Test1234!"})
        assert resp.status_code == 422


class TestGetMe:
    @pytest.mark.asyncio
    async def test_without_token_returns_401_or_403(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_with_valid_token_returns_user(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == registered_user["email"]
        assert data["name"] == registered_user["name"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_response_never_exposes_password_hash(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert "password_hash" not in resp.json()

    @pytest.mark.asyncio
    async def test_response_never_exposes_totp_secret(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert "totp_secret" not in resp.json()

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/auth/me", headers={"Authorization": "Bearer totally.fake.token"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_bearer_returns_401_or_403(self, client: AsyncClient):
        resp = await client.get("/auth/me", headers={"Authorization": "NotBearer token"})
        assert resp.status_code in (401, 403)


class TestRefresh:
    @pytest.mark.asyncio
    async def test_returns_new_access_token(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        import asyncio

        login = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        old_token = login.json()["access_token"]
        refresh_token = login.json()["refresh_token"]

        await asyncio.sleep(1)

        resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert resp.json()["access_token"] != old_token

    @pytest.mark.asyncio
    async def test_new_token_is_valid(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        login = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        refresh_token = login.json()["refresh_token"]

        refresh_resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        new_access = refresh_resp.json()["access_token"]

        me_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
        assert me_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.post("/auth/refresh", json={"refresh_token": "invalid_token_here"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_used_token_returns_401(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        login = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        refresh_token = login.json()["refresh_token"]

        await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_used_token_does_not_return_new_token(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        login = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        refresh_token = login.json()["refresh_token"]

        await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert "access_token" not in resp.json() or resp.status_code != 200


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_returns_200(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        login = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        refresh_token = login.json()["refresh_token"]

        resp = await client.post("/auth/logout", json={"refresh_token": refresh_token}, headers=auth_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_invalidates_refresh_token(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        login = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        refresh_token = login.json()["refresh_token"]

        await client.post("/auth/logout", json={"refresh_token": refresh_token}, headers=auth_headers)
        resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_does_not_invalidate_other_tokens(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        login1 = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        login2 = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        rt1 = login1.json()["refresh_token"]
        rt2 = login2.json()["refresh_token"]

        await client.post("/auth/logout", json={"refresh_token": rt1}, headers=auth_headers)
        resp = await client.post("/auth/refresh", json={"refresh_token": rt2})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_all_returns_200(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/auth/logout-all", headers=auth_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_all_invalidates_all_tokens(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        login1 = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        login2 = await client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        rt1 = login1.json()["refresh_token"]
        rt2 = login2.json()["refresh_token"]

        await client.post("/auth/logout-all", headers=auth_headers)

        assert (await client.post("/auth/refresh", json={"refresh_token": rt1})).status_code == 401
        assert (await client.post("/auth/refresh", json={"refresh_token": rt2})).status_code == 401

    @pytest.mark.asyncio
    async def test_logout_all_requires_auth(self, client: AsyncClient):
        resp = await client.post("/auth/logout-all")
        assert resp.status_code in (401, 403)


class TestChangePassword:
    @pytest.mark.asyncio
    async def test_success_returns_200(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        resp = await client.post(
            "/auth/change-password",
            headers=auth_headers,
            json={"current_password": registered_user["password"], "new_password": "NewPass456!", "new_password_confirm": "NewPass456!"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_allows_login_with_new_password(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        await client.post(
            "/auth/change-password",
            headers=auth_headers,
            json={"current_password": registered_user["password"], "new_password": "NewPass456!", "new_password_confirm": "NewPass456!"},
        )
        resp = await client.post("/auth/login", json={"email": registered_user["email"], "password": "NewPass456!"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_blocks_login_with_old_password(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        await client.post(
            "/auth/change-password",
            headers=auth_headers,
            json={"current_password": registered_user["password"], "new_password": "NewPass456!", "new_password_confirm": "NewPass456!"},
        )
        resp = await client.post("/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_revokes_existing_refresh_tokens(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        login = await client.post("/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]})
        rt = login.json()["refresh_token"]

        await client.post(
            "/auth/change-password",
            headers=auth_headers,
            json={"current_password": registered_user["password"], "new_password": "NewPass456!", "new_password_confirm": "NewPass456!"},
        )

        resp = await client.post("/auth/refresh", json={"refresh_token": rt})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_current_password_returns_400(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/auth/change-password",
            headers=auth_headers,
            json={"current_password": "WrongCurrent1!", "new_password": "NewPass456!", "new_password_confirm": "NewPass456!"},
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "PASSWORD_MISMATCH"

    @pytest.mark.asyncio
    async def test_wrong_current_password_does_not_change_password(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        await client.post(
            "/auth/change-password",
            headers=auth_headers,
            json={"current_password": "WrongCurrent1!", "new_password": "NewPass456!", "new_password_confirm": "NewPass456!"},
        )
        resp = await client.post("/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_new_passwords_mismatch_returns_422(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        resp = await client.post(
            "/auth/change-password",
            headers=auth_headers,
            json={"current_password": registered_user["password"], "new_password": "NewPass456!", "new_password_confirm": "Different789@"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/auth/change-password",
            json={"current_password": registered_user["password"], "new_password": "NewPass456!", "new_password_confirm": "NewPass456!"},
        )
        assert resp.status_code in (401, 403)


class TestForgotPassword:
    @pytest.mark.asyncio
    async def test_nonexistent_email_still_returns_200(self, client: AsyncClient):
        resp = await client.post("/auth/forgot-password?email=ghost@example.com")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_existing_email_returns_200(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(f"/auth/forgot-password?email={registered_user['email']}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_nonexistent_and_existing_same_response_shape(self, client: AsyncClient, registered_user: dict):
        ghost = await client.post("/auth/forgot-password?email=ghost@example.com")
        real = await client.post(f"/auth/forgot-password?email={registered_user['email']}")
        assert ghost.status_code == real.status_code
        assert set(ghost.json().keys()) == set(real.json().keys())


class TestResendVerification:
    @pytest.mark.asyncio
    async def test_nonexistent_email_returns_200(self, client: AsyncClient):
        resp = await client.post("/auth/resend-verification-email?email=ghost@example.com")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_unverified_user_returns_200(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(f"/auth/resend-verification-email?email={registered_user['email']}")
        assert resp.status_code == 200
