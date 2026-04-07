from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest

from src.core.exceptions import (
    EmailAlreadyExistsError,
    EmailAlreadyVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidTwoFactorCodeError,
    NotFoundError,
    PasswordMismatchError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
    UserInactiveError,
)
from src.models.user import RefreshToken, User
from src.schemas.auth import ChangePasswordRequest
from src.services.auth import AuthService


@pytest.fixture
def user_repo():
    return AsyncMock()


@pytest.fixture
def token_repo():
    return AsyncMock()


@pytest.fixture
def mail_service():
    return MagicMock()


@pytest.fixture
def totp_service():
    return MagicMock()


@pytest.fixture
def auth_service(user_repo, token_repo, mail_service, totp_service):
    return AuthService(user_repo, token_repo, mail_service, totp_service)


@pytest.fixture
def active_user():
    u = MagicMock(spec=User)
    u.id = 1
    u.email = "test@example.com"
    u.name = "Test User"
    u.is_active = True
    u.is_verified = True
    u.is_2fa_enabled = False
    u.totp_secret = None
    u.password_hash = None
    u.oauth_provider = None
    return u


@pytest.fixture
def inactive_user(active_user):
    active_user.is_active = False
    return active_user


@pytest.fixture
def user_with_2fa(active_user):
    active_user.is_2fa_enabled = True
    active_user.totp_secret = "BASE32SECRET"
    return active_user


@pytest.fixture
def user_with_password(auth_service, active_user):
    active_user.password_hash = auth_service.hash_password("Secret123!")
    return active_user


@pytest.fixture
def active_db_token():
    t = MagicMock(spec=RefreshToken)
    t.user_id = 1
    t.expires_at = datetime.now(UTC) + timedelta(days=7)
    t.is_revoked = False
    return t


@pytest.fixture
def expired_db_token():
    t = MagicMock(spec=RefreshToken)
    t.user_id = 1
    t.expires_at = datetime.now(UTC) - timedelta(days=1)
    t.is_revoked = False
    return t


@pytest.fixture
def change_password_req():
    return ChangePasswordRequest(
        current_password="Secret123!",
        new_password="NewPass456!",
        new_password_confirm="NewPass456!",
    )


class TestPassword:
    def test_hash_and_verify_success(self, auth_service):
        hashed = auth_service.hash_password("Secret123!")
        assert auth_service.verify_password("Secret123!", hashed)

    def test_verify_wrong_password_returns_false(self, auth_service):
        hashed = auth_service.hash_password("Secret123!")
        assert not auth_service.verify_password("WrongPass!", hashed)

    def test_two_hashes_of_same_password_differ(self, auth_service):
        h1 = auth_service.hash_password("Secret123!")
        h2 = auth_service.hash_password("Secret123!")
        assert h1 != h2  



class TestTokens:
    def test_create_and_decode_access_token(self, auth_service, active_user):
        token = auth_service.create_access_token(active_user)
        payload = AuthService.decode_access_token(token)
        assert payload["sub"] == str(active_user.id)
        assert payload["email"] == active_user.email
        assert payload["type"] == "access"

    def test_decode_expired_token_raises(self, auth_service):
        s = auth_service.settings
        payload = {
            "sub": "1",
            "email": "test@example.com",
            "type": "access",
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        token = jwt.encode(payload, s.secret_key, algorithm=s.algorithm)
        with pytest.raises(InvalidTokenError, match="expired"):
            AuthService.decode_access_token(token)

    def test_decode_wrong_type_raises(self, auth_service):
        s = auth_service.settings
        payload = {
            "sub": "1",
            "type": "2fa",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(payload, s.secret_key, algorithm=s.algorithm)
        with pytest.raises(InvalidTokenError):
            AuthService.decode_access_token(token)

    def test_decode_garbage_token_raises(self):
        with pytest.raises(InvalidTokenError):
            AuthService.decode_access_token("not.a.real.token")

    def test_create_2fa_token_decoded_correctly(self, auth_service, active_user):
        token = auth_service.create_2fa_token(active_user)
        payload = AuthService.decode_2fa_token(token)
        assert payload["sub"] == str(active_user.id)
        assert payload["type"] == "2fa"

    def test_access_token_rejected_as_2fa_token(self, auth_service, active_user):
        token = auth_service.create_access_token(active_user)
        with pytest.raises(InvalidTokenError):
            AuthService.decode_2fa_token(token)

    def test_2fa_token_rejected_as_access_token(self, auth_service, active_user):
        token = auth_service.create_2fa_token(active_user)
        with pytest.raises(InvalidTokenError):
            AuthService.decode_access_token(token)

    def test_tampered_token_raises(self, auth_service, active_user):
        token = auth_service.create_access_token(active_user)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(InvalidTokenError):
            AuthService.decode_access_token(tampered)



class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success_creates_user(self, auth_service, user_repo, active_user):
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = active_user
        bg = MagicMock()

        await auth_service.register_user("Name", "new@example.com", "Secret123!", bg)

        user_repo.create.assert_called_once()
        kwargs = user_repo.create.call_args.kwargs
        assert kwargs["email"] == "new@example.com"
        assert kwargs["name"] == "Name"
        assert kwargs["password_hash"] != "Secret123!"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self, auth_service, user_repo, active_user):
        user_repo.get_by_email.return_value = active_user

        with pytest.raises(EmailAlreadyExistsError):
            await auth_service.register_user("Name", "dupe@example.com", "Secret123!", MagicMock())

        user_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_sends_verification_email(self, auth_service, user_repo, mail_service):
        new_user = MagicMock(spec=User, id=5, email="user@example.com", name="Name")
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = new_user
        bg = MagicMock()

        await auth_service.register_user("Name", "user@example.com", "Secret123!", bg)

        bg.add_task.assert_called_once_with(
            mail_service.send_verification_email,
            user_id=5,
            user_email="user@example.com",
            name="Name",
        )

    @pytest.mark.asyncio
    async def test_register_duplicate_does_not_send_email(self, auth_service, user_repo, active_user):
        user_repo.get_by_email.return_value = active_user
        bg = MagicMock()

        with pytest.raises(EmailAlreadyExistsError):
            await auth_service.register_user("Name", active_user.email, "Secret123!", bg)

        bg.add_task.assert_not_called()

class TestAuthenticate:
    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(self, auth_service, user_repo, token_repo, user_with_password):
        user_repo.get_by_email.return_value = user_with_password
        token_repo.create.return_value = MagicMock()

        result = await auth_service.authenticate_user("test@example.com", "Secret123!")

        assert result.token_type == "bearer"
        assert result.access_token
        assert result.refresh_token is not None

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_raises(self, auth_service, user_repo):
        user_repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user("nobody@example.com", "Secret123!")

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self, auth_service, user_repo, user_with_password):
        user_repo.get_by_email.return_value = user_with_password

        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user("test@example.com", "Wrong123!")

    @pytest.mark.asyncio
    async def test_login_inactive_user_raises(self, auth_service, user_repo, inactive_user):
        inactive_user.password_hash = auth_service.hash_password("Secret123!")
        user_repo.get_by_email.return_value = inactive_user

        with pytest.raises(UserInactiveError):
            await auth_service.authenticate_user("test@example.com", "Secret123!")

    @pytest.mark.asyncio
    async def test_login_inactive_user_does_not_issue_tokens(self, auth_service, user_repo, token_repo, inactive_user):
        inactive_user.password_hash = auth_service.hash_password("Secret123!")
        user_repo.get_by_email.return_value = inactive_user

        with pytest.raises(UserInactiveError):
            await auth_service.authenticate_user("test@example.com", "Secret123!")

        token_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_oauth_user_no_password_raises(self, auth_service, user_repo, active_user):
        active_user.oauth_provider = "google"
        active_user.password_hash = None
        user_repo.get_by_email.return_value = active_user

        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user("test@example.com", "Secret123!")

    @pytest.mark.asyncio
    async def test_login_2fa_enabled_returns_temp_token(self, auth_service, user_repo, user_with_2fa):
        user_with_2fa.password_hash = auth_service.hash_password("Secret123!")
        user_repo.get_by_email.return_value = user_with_2fa

        result = await auth_service.authenticate_user("test@example.com", "Secret123!")

        assert result.token_type == "2fa_required"
        assert result.refresh_token is None
        assert result.expires_in == 5 * 60

    @pytest.mark.asyncio
    async def test_login_2fa_temp_token_is_not_access_token(self, auth_service, user_repo, user_with_2fa):
        user_with_2fa.password_hash = auth_service.hash_password("Secret123!")
        user_repo.get_by_email.return_value = user_with_2fa

        result = await auth_service.authenticate_user("test@example.com", "Secret123!")

        with pytest.raises(InvalidTokenError):
            AuthService.decode_access_token(result.access_token)

    @pytest.mark.asyncio
    async def test_login_passes_device_info_to_token_repo(self, auth_service, user_repo, token_repo, user_with_password):
        user_repo.get_by_email.return_value = user_with_password
        token_repo.create.return_value = MagicMock()

        await auth_service.authenticate_user("test@example.com", "Secret123!", device_info="Chrome/iPhone")

        call_args = token_repo.create.call_args.args
        assert "Chrome/iPhone" in call_args



class TestRefreshToken:
    @pytest.mark.asyncio
    async def test_refresh_success_rotates_token(self, auth_service, user_repo, token_repo, active_db_token, active_user):
        token_repo.get_active_token.return_value = active_db_token
        user_repo.get_by_id.return_value = active_user
        token_repo.create.return_value = MagicMock()

        result = await auth_service.refresh_access_token("old_token")

        assert result.token_type == "bearer"
        assert result.access_token
        token_repo.mark_as_revoked.assert_called_once_with(active_db_token)

    @pytest.mark.asyncio
    async def test_refresh_creates_new_token(self, auth_service, user_repo, token_repo, active_db_token, active_user):
        token_repo.get_active_token.return_value = active_db_token
        user_repo.get_by_id.return_value = active_user
        token_repo.create.return_value = MagicMock()

        await auth_service.refresh_access_token("old_token")

        token_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_raises(self, auth_service, token_repo):
        token_repo.get_active_token.return_value = None

        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_access_token("bad_token")

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_does_not_create_new(self, auth_service, token_repo):
        token_repo.get_active_token.return_value = None

        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_access_token("bad_token")

        token_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_expired_db_token_raises_and_revokes(self, auth_service, token_repo, expired_db_token):
        token_repo.get_active_token.return_value = expired_db_token

        with pytest.raises(InvalidTokenError, match="expired"):
            await auth_service.refresh_access_token("expired_token")

        token_repo.mark_as_revoked.assert_called_once_with(expired_db_token)

    @pytest.mark.asyncio
    async def test_refresh_inactive_user_raises(self, auth_service, user_repo, token_repo, active_db_token, inactive_user):
        token_repo.get_active_token.return_value = active_db_token
        user_repo.get_by_id.return_value = inactive_user

        with pytest.raises(UserInactiveError):
            await auth_service.refresh_access_token("valid_token")

    @pytest.mark.asyncio
    async def test_refresh_inactive_user_does_not_create_token(self, auth_service, user_repo, token_repo, active_db_token, inactive_user):
        token_repo.get_active_token.return_value = active_db_token
        user_repo.get_by_id.return_value = inactive_user

        with pytest.raises(UserInactiveError):
            await auth_service.refresh_access_token("valid_token")

        token_repo.create.assert_not_called()


class TestChangePassword:
    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, user_repo, token_repo, active_user, change_password_req):
        active_user.password_hash = auth_service.hash_password("Secret123!")
        user_repo.get_by_id.return_value = active_user

        await auth_service.change_password(change_password_req, 1)

        user_repo.update_password.assert_called_once()
        new_hash = user_repo.update_password.call_args.args[1]
        assert auth_service.verify_password("NewPass456!", new_hash)

    @pytest.mark.asyncio
    async def test_change_password_revokes_all_sessions(self, auth_service, user_repo, token_repo, active_user, change_password_req):
        active_user.password_hash = auth_service.hash_password("Secret123!")
        user_repo.get_by_id.return_value = active_user

        await auth_service.change_password(change_password_req, 1)

        token_repo.revoke_all_for_user.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_raises(self, auth_service, user_repo, active_user):
        active_user.password_hash = auth_service.hash_password("Secret123!")
        user_repo.get_by_id.return_value = active_user
        req = ChangePasswordRequest(
            current_password="WrongPass!1",
            new_password="NewPass456!",
            new_password_confirm="NewPass456!",
        )

        with pytest.raises(PasswordMismatchError):
            await auth_service.change_password(req, 1)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_does_not_update(self, auth_service, user_repo, token_repo, active_user):
        active_user.password_hash = auth_service.hash_password("Secret123!")
        user_repo.get_by_id.return_value = active_user
        req = ChangePasswordRequest(
            current_password="WrongPass!1",
            new_password="NewPass456!",
            new_password_confirm="NewPass456!",
        )

        with pytest.raises(PasswordMismatchError):
            await auth_service.change_password(req, 1)

        user_repo.update_password.assert_not_called()
        token_repo.revoke_all_for_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_change_password_user_not_found_raises(self, auth_service, user_repo, change_password_req):
        user_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await auth_service.change_password(change_password_req, 999)

    @pytest.mark.asyncio
    async def test_change_password_user_not_found_does_not_update(self, auth_service, user_repo, token_repo, change_password_req):
        user_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await auth_service.change_password(change_password_req, 999)

        user_repo.update_password.assert_not_called()
        token_repo.revoke_all_for_user.assert_not_called()



class TestTwoFactor:
    @pytest.mark.asyncio
    async def test_enable_2fa_success(self, auth_service, user_repo, totp_service, active_user):
        user_repo.get_by_id.return_value = active_user
        totp_service.generate_totp_secret.return_value = "BASE32SECRET"
        totp_service.get_totp_uri.return_value = "otpauth://totp/..."
        totp_service.generate_qr_code_base64.return_value = "base64qrstring"

        result = await auth_service.enable_2fa(1)

        assert result.secret == "BASE32SECRET"
        assert result.qr_code_base64 == "base64qrstring"
        user_repo.update_totp_secret.assert_called_once_with(1, "BASE32SECRET")

    @pytest.mark.asyncio
    async def test_enable_2fa_already_enabled_raises(self, auth_service, user_repo, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa

        with pytest.raises(TwoFactorAlreadyEnabledError):
            await auth_service.enable_2fa(1)

    @pytest.mark.asyncio
    async def test_enable_2fa_already_enabled_does_not_overwrite_secret(self, auth_service, user_repo, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa

        with pytest.raises(TwoFactorAlreadyEnabledError):
            await auth_service.enable_2fa(1)

        user_repo.update_totp_secret.assert_not_called()

    @pytest.mark.asyncio
    async def test_enable_2fa_user_not_found_raises(self, auth_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await auth_service.enable_2fa(999)

    @pytest.mark.asyncio
    async def test_confirm_2fa_success(self, auth_service, user_repo, totp_service, active_user):
        active_user.totp_secret = "BASE32SECRET"
        user_repo.get_by_id.return_value = active_user
        totp_service.verify_totp.return_value = True

        await auth_service.confirm_2fa_setup(1, "123456")

        user_repo.update_2fa_enabled.assert_called_once_with(1, True)

    @pytest.mark.asyncio
    async def test_confirm_2fa_invalid_code_raises(self, auth_service, user_repo, totp_service, active_user):
        active_user.totp_secret = "BASE32SECRET"
        user_repo.get_by_id.return_value = active_user
        totp_service.verify_totp.return_value = False

        with pytest.raises(InvalidTwoFactorCodeError):
            await auth_service.confirm_2fa_setup(1, "000000")

    @pytest.mark.asyncio
    async def test_confirm_2fa_invalid_code_does_not_enable(self, auth_service, user_repo, totp_service, active_user):
        active_user.totp_secret = "BASE32SECRET"
        user_repo.get_by_id.return_value = active_user
        totp_service.verify_totp.return_value = False

        with pytest.raises(InvalidTwoFactorCodeError):
            await auth_service.confirm_2fa_setup(1, "000000")

        user_repo.update_2fa_enabled.assert_not_called()

    @pytest.mark.asyncio
    async def test_confirm_2fa_no_secret_raises(self, auth_service, user_repo, active_user):
        active_user.totp_secret = None
        user_repo.get_by_id.return_value = active_user

        with pytest.raises(TwoFactorNotEnabledError):
            await auth_service.confirm_2fa_setup(1, "123456")

    @pytest.mark.asyncio
    async def test_disable_2fa_success(self, auth_service, user_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = True

        await auth_service.disable_2fa(1, "123456")

        user_repo.update_2fa_enabled.assert_called_once_with(1, False)
        user_repo.update_totp_secret.assert_called_once_with(1, None)

    @pytest.mark.asyncio
    async def test_disable_2fa_invalid_code_raises(self, auth_service, user_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = False

        with pytest.raises(InvalidTwoFactorCodeError):
            await auth_service.disable_2fa(1, "000000")

    @pytest.mark.asyncio
    async def test_disable_2fa_invalid_code_does_not_disable(self, auth_service, user_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = False

        with pytest.raises(InvalidTwoFactorCodeError):
            await auth_service.disable_2fa(1, "000000")

        user_repo.update_2fa_enabled.assert_not_called()
        user_repo.update_totp_secret.assert_not_called()

    @pytest.mark.asyncio
    async def test_disable_2fa_not_enabled_raises(self, auth_service, user_repo, active_user):
        active_user.is_2fa_enabled = False
        active_user.totp_secret = None
        user_repo.get_by_id.return_value = active_user

        with pytest.raises(TwoFactorNotEnabledError):
            await auth_service.disable_2fa(1, "123456")

    @pytest.mark.asyncio
    async def test_verify_2fa_token_success(self, auth_service, user_repo, token_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = True
        token_repo.create.return_value = MagicMock()

        temp_token = auth_service.create_2fa_token(user_with_2fa)
        result = await auth_service.verify_2fa_token(temp_token, "123456")

        assert result.token_type == "bearer"
        assert result.access_token
        assert result.refresh_token is not None

    @pytest.mark.asyncio
    async def test_verify_2fa_wrong_code_raises(self, auth_service, user_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = False

        temp_token = auth_service.create_2fa_token(user_with_2fa)
        with pytest.raises(InvalidTwoFactorCodeError):
            await auth_service.verify_2fa_token(temp_token, "000000")

    @pytest.mark.asyncio
    async def test_verify_2fa_wrong_code_does_not_issue_tokens(self, auth_service, user_repo, token_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = False

        temp_token = auth_service.create_2fa_token(user_with_2fa)
        with pytest.raises(InvalidTwoFactorCodeError):
            await auth_service.verify_2fa_token(temp_token, "000000")

        token_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_2fa_invalid_temp_token_raises(self, auth_service):
        with pytest.raises(InvalidTokenError):
            await auth_service.verify_2fa_token("garbage.token.here", "123456")

    @pytest.mark.asyncio
    async def test_verify_2fa_access_token_as_temp_raises(self, auth_service, user_repo, active_user):
        user_repo.get_by_id.return_value = active_user
        access_token = auth_service.create_access_token(active_user)

        with pytest.raises(InvalidTokenError):
            await auth_service.verify_2fa_token(access_token, "123456")


class TestVerifyEmail:
    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_service, user_repo, mail_service, active_user):
        active_user.is_verified = False
        user_repo.get_by_id.return_value = active_user
        mail_service.decode_email_token.return_value = {"sub": "1"}

        await auth_service.verify_email("valid_token")

        user_repo.mark_as_verified.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_verify_email_already_verified_raises(self, auth_service, user_repo, mail_service, active_user):
        active_user.is_verified = True
        user_repo.get_by_id.return_value = active_user
        mail_service.decode_email_token.return_value = {"sub": "1"}

        with pytest.raises(EmailAlreadyVerifiedError):
            await auth_service.verify_email("valid_token")

    @pytest.mark.asyncio
    async def test_verify_email_already_verified_does_not_re_verify(self, auth_service, user_repo, mail_service, active_user):
        active_user.is_verified = True
        user_repo.get_by_id.return_value = active_user
        mail_service.decode_email_token.return_value = {"sub": "1"}

        with pytest.raises(EmailAlreadyVerifiedError):
            await auth_service.verify_email("valid_token")

        user_repo.mark_as_verified.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found_raises(self, auth_service, user_repo, mail_service):
        user_repo.get_by_id.return_value = None
        mail_service.decode_email_token.return_value = {"sub": "999"}

        with pytest.raises(NotFoundError):
            await auth_service.verify_email("valid_token")

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token_raises(self, auth_service, mail_service):
        mail_service.decode_email_token.side_effect = InvalidTokenError("bad token")

        with pytest.raises(InvalidTokenError):
            await auth_service.verify_email("bad_token")