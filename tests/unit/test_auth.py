from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest

from src.auth.application.commands import (
    ChangePasswordCommand,
    Confirm2FACommand,
    Disable2FACommand,
    Enable2FACommand,
    LoginCommand,
    RefreshTokenCommand,
    RegisterCommand,
    VerifyEmailCommand,
    Verify2FAAndLoginCommand,
)
from src.auth.application.handlers.change_password import ChangePasswordCommandHandler
from src.auth.application.handlers.login import LoginCommandHandler
from src.auth.application.handlers.refresh_token import RefreshTokenCommandHandler
from src.auth.application.handlers.register import RegisterCommandHandler
from src.auth.application.handlers.two_factor import (
    Confirm2FACommandHandler,
    Disable2FACommandHandler,
    Enable2FACommandHandler,
    Verify2FAAndLoginCommandHandler,
)
from src.auth.application.handlers.verify_email import VerifyEmailCommandHandler
from src.auth.application.token_utils import PasswordUtils, TokenUtils
from src.auth.domain.errors import (
    EmailAlreadyExistsError,
    EmailAlreadyVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidTwoFactorCodeError,
    PasswordMismatchError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
    UserInactiveError,
    UserNotFoundError,
)
from src.auth.domain.models import RefreshTokenDomain, UserDomain
from src.core.config import get_settings

_pw = PasswordUtils()


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
def active_user():
    return UserDomain(
        id=1,
        name="Test User",
        email="test@example.com",
        password_hash=None,
        is_verified=True,
        is_active=True,
        oauth_provider=None,
        oauth_provider_id=None,
        avatar_url=None,
        totp_secret=None,
        is_2fa_enabled=False,
    )


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
def user_with_password(active_user):
    active_user.password_hash = _pw.hash("Secret123!")
    return active_user


@pytest.fixture
def active_db_token():
    return RefreshTokenDomain(
        id=1,
        token="active_refresh_token",
        user_id=1,
        expires_at=datetime.now(UTC) + timedelta(days=7),
        is_revoked=False,
        device_info=None,
    )


@pytest.fixture
def expired_db_token():
    return RefreshTokenDomain(
        id=2,
        token="expired_refresh_token",
        user_id=1,
        expires_at=datetime.now(UTC) - timedelta(days=1),
        is_revoked=False,
        device_info=None,
    )


class TestPasswordUtils:
    def test_hash_and_verify_success(self):
        hashed = _pw.hash("Secret123!")
        assert _pw.verify("Secret123!", hashed)

    def test_verify_wrong_password_returns_false(self):
        hashed = _pw.hash("Secret123!")
        assert not _pw.verify("WrongPass!", hashed)

    def test_two_hashes_of_same_password_differ(self):
        h1 = _pw.hash("Secret123!")
        h2 = _pw.hash("Secret123!")
        assert h1 != h2


class TestTokenUtils:
    def test_create_and_decode_access_token(self, active_user):
        token = TokenUtils.create_access_token(active_user.id, active_user.email)
        payload = TokenUtils.decode_access_token(token)
        assert payload["sub"] == str(active_user.id)
        assert payload["email"] == active_user.email
        assert payload["type"] == "access"

    def test_decode_expired_token_raises(self):
        s = get_settings()
        payload = {
            "sub": "1",
            "email": "test@example.com",
            "type": "access",
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        token = jwt.encode(payload, s.secret_key, algorithm=s.algorithm)
        with pytest.raises(InvalidTokenError, match="expired"):
            TokenUtils.decode_access_token(token)

    def test_decode_wrong_type_raises(self):
        s = get_settings()
        payload = {
            "sub": "1",
            "type": "2fa",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(payload, s.secret_key, algorithm=s.algorithm)
        with pytest.raises(InvalidTokenError):
            TokenUtils.decode_access_token(token)

    def test_decode_garbage_token_raises(self):
        with pytest.raises(InvalidTokenError):
            TokenUtils.decode_access_token("not.a.real.token")

    def test_create_2fa_token_decoded_correctly(self, active_user):
        token = TokenUtils.create_2fa_token(active_user.id, active_user.email)
        payload = TokenUtils.decode_2fa_token(token)
        assert payload["sub"] == str(active_user.id)
        assert payload["type"] == "2fa"

    def test_access_token_rejected_as_2fa_token(self, active_user):
        token = TokenUtils.create_access_token(active_user.id, active_user.email)
        with pytest.raises(InvalidTokenError):
            TokenUtils.decode_2fa_token(token)

    def test_2fa_token_rejected_as_access_token(self, active_user):
        token = TokenUtils.create_2fa_token(active_user.id, active_user.email)
        with pytest.raises(InvalidTokenError):
            TokenUtils.decode_access_token(token)

    def test_tampered_token_raises(self, active_user):
        token = TokenUtils.create_access_token(active_user.id, active_user.email)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(InvalidTokenError):
            TokenUtils.decode_access_token(tampered)


class TestRegisterCommandHandler:
    @pytest.fixture
    def handler(self, user_repo, mail_service):
        return RegisterCommandHandler(user_repo, mail_service, _pw)

    @pytest.mark.asyncio
    async def test_register_success_creates_user(self, handler, user_repo, active_user):
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = active_user
        bg = MagicMock()

        await handler.handle(RegisterCommand(name="Name", email="new@example.com", password="Secret123!"), bg)

        user_repo.create.assert_called_once()
        kwargs = user_repo.create.call_args.kwargs
        assert kwargs["email"] == "new@example.com"
        assert kwargs["name"] == "Name"
        assert kwargs["password_hash"] != "Secret123!"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self, handler, user_repo, active_user):
        user_repo.get_by_email.return_value = active_user

        with pytest.raises(EmailAlreadyExistsError):
            await handler.handle(
                RegisterCommand(name="Name", email="dupe@example.com", password="Secret123!"),
                MagicMock(),
            )

        user_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_sends_verification_email(self, handler, user_repo, mail_service):
        new_user = UserDomain(
            id=5,
            name="Name",
            email="user@example.com",
            password_hash=None,
            is_verified=False,
            is_active=True,
            oauth_provider=None,
            oauth_provider_id=None,
            avatar_url=None,
            totp_secret=None,
            is_2fa_enabled=False,
        )
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = new_user
        bg = MagicMock()

        await handler.handle(RegisterCommand(name="Name", email="user@example.com", password="Secret123!"), bg)

        bg.add_task.assert_called_once_with(
            mail_service.send_verification_email,
            user_id=5,
            user_email="user@example.com",
            name="Name",
        )

    @pytest.mark.asyncio
    async def test_register_duplicate_does_not_send_email(self, handler, user_repo, active_user):
        user_repo.get_by_email.return_value = active_user
        bg = MagicMock()

        with pytest.raises(EmailAlreadyExistsError):
            await handler.handle(
                RegisterCommand(name="Name", email=active_user.email, password="Secret123!"),
                bg,
            )

        bg.add_task.assert_not_called()


class TestLoginCommandHandler:
    @pytest.fixture
    def handler(self, user_repo, token_repo):
        return LoginCommandHandler(user_repo, token_repo, _pw)

    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(self, handler, user_repo, token_repo, user_with_password):
        user_repo.get_by_email.return_value = user_with_password
        token_repo.create.return_value = MagicMock()

        result = await handler.handle(LoginCommand(email="test@example.com", password="Secret123!"))

        assert result.token_type == "bearer"
        assert result.access_token
        assert result.refresh_token is not None

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_raises(self, handler, user_repo):
        user_repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await handler.handle(LoginCommand(email="nobody@example.com", password="Secret123!"))

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self, handler, user_repo, user_with_password):
        user_repo.get_by_email.return_value = user_with_password

        with pytest.raises(InvalidCredentialsError):
            await handler.handle(LoginCommand(email="test@example.com", password="Wrong123!"))

    @pytest.mark.asyncio
    async def test_login_inactive_user_raises(self, handler, user_repo, inactive_user):
        inactive_user.password_hash = _pw.hash("Secret123!")
        user_repo.get_by_email.return_value = inactive_user

        with pytest.raises(UserInactiveError):
            await handler.handle(LoginCommand(email="test@example.com", password="Secret123!"))

    @pytest.mark.asyncio
    async def test_login_inactive_user_does_not_issue_tokens(self, handler, user_repo, token_repo, inactive_user):
        inactive_user.password_hash = _pw.hash("Secret123!")
        user_repo.get_by_email.return_value = inactive_user

        with pytest.raises(UserInactiveError):
            await handler.handle(LoginCommand(email="test@example.com", password="Secret123!"))

        token_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_oauth_user_no_password_raises(self, handler, user_repo, active_user):
        active_user.oauth_provider = "google"
        active_user.password_hash = None
        user_repo.get_by_email.return_value = active_user

        with pytest.raises(InvalidCredentialsError):
            await handler.handle(LoginCommand(email="test@example.com", password="Secret123!"))

    @pytest.mark.asyncio
    async def test_login_2fa_enabled_returns_temp_token(self, handler, user_repo, user_with_2fa):
        user_with_2fa.password_hash = _pw.hash("Secret123!")
        user_repo.get_by_email.return_value = user_with_2fa

        result = await handler.handle(LoginCommand(email="test@example.com", password="Secret123!"))

        assert result.token_type == "2fa_required"
        assert result.refresh_token is None

    @pytest.mark.asyncio
    async def test_login_2fa_temp_token_is_not_access_token(self, handler, user_repo, user_with_2fa):
        user_with_2fa.password_hash = _pw.hash("Secret123!")
        user_repo.get_by_email.return_value = user_with_2fa

        result = await handler.handle(LoginCommand(email="test@example.com", password="Secret123!"))

        with pytest.raises(InvalidTokenError):
            TokenUtils.decode_access_token(result.access_token)

    @pytest.mark.asyncio
    async def test_login_passes_device_info_to_token_repo(self, handler, user_repo, token_repo, user_with_password):
        user_repo.get_by_email.return_value = user_with_password
        token_repo.create.return_value = MagicMock()

        await handler.handle(LoginCommand(email="test@example.com", password="Secret123!", device_info="Chrome/iPhone"))

        call_args = token_repo.create.call_args
        assert "Chrome/iPhone" in str(call_args)


class TestRefreshTokenCommandHandler:
    @pytest.fixture
    def handler(self, user_repo, token_repo):
        return RefreshTokenCommandHandler(user_repo, token_repo)

    @pytest.mark.asyncio
    async def test_refresh_success_rotates_token(self, handler, user_repo, token_repo, active_db_token, active_user):
        token_repo.get_active_token.return_value = active_db_token
        user_repo.get_by_id.return_value = active_user
        token_repo.create.return_value = MagicMock()

        result = await handler.handle(RefreshTokenCommand(refresh_token="old_token"))

        assert result.token_type == "bearer"
        assert result.access_token
        assert active_db_token.is_revoked is True
        token_repo.save.assert_called()

    @pytest.mark.asyncio
    async def test_refresh_creates_new_token(self, handler, user_repo, token_repo, active_db_token, active_user):
        token_repo.get_active_token.return_value = active_db_token
        user_repo.get_by_id.return_value = active_user
        token_repo.create.return_value = MagicMock()

        await handler.handle(RefreshTokenCommand(refresh_token="old_token"))

        token_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_raises(self, handler, token_repo):
        token_repo.get_active_token.return_value = None

        with pytest.raises(InvalidTokenError):
            await handler.handle(RefreshTokenCommand(refresh_token="bad_token"))

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_does_not_create_new(self, handler, token_repo):
        token_repo.get_active_token.return_value = None

        with pytest.raises(InvalidTokenError):
            await handler.handle(RefreshTokenCommand(refresh_token="bad_token"))

        token_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_expired_db_token_raises_and_revokes(self, handler, token_repo, expired_db_token):
        token_repo.get_active_token.return_value = expired_db_token

        with pytest.raises(InvalidTokenError, match="expired"):
            await handler.handle(RefreshTokenCommand(refresh_token="expired_token"))

        assert expired_db_token.is_revoked is True
        token_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_inactive_user_raises(self, handler, user_repo, token_repo, active_db_token, inactive_user):
        token_repo.get_active_token.return_value = active_db_token
        user_repo.get_by_id.return_value = inactive_user

        with pytest.raises(UserInactiveError):
            await handler.handle(RefreshTokenCommand(refresh_token="valid_token"))

    @pytest.mark.asyncio
    async def test_refresh_inactive_user_does_not_create_token(self, handler, user_repo, token_repo, active_db_token, inactive_user):
        token_repo.get_active_token.return_value = active_db_token
        user_repo.get_by_id.return_value = inactive_user

        with pytest.raises(UserInactiveError):
            await handler.handle(RefreshTokenCommand(refresh_token="valid_token"))

        token_repo.create.assert_not_called()


class TestChangePasswordCommandHandler:
    @pytest.fixture
    def handler(self, user_repo, token_repo):
        return ChangePasswordCommandHandler(user_repo, token_repo, _pw)

    @pytest.mark.asyncio
    async def test_change_password_success(self, handler, user_repo, token_repo, active_user):
        active_user.password_hash = _pw.hash("Secret123!")
        user_repo.get_by_id.return_value = active_user
        user_repo.save.return_value = active_user

        await handler.handle(ChangePasswordCommand(user_id=1, current_password="Secret123!", new_password="NewPass456!"))

        user_repo.save.assert_called_once()
        assert _pw.verify("NewPass456!", active_user.password_hash)

    @pytest.mark.asyncio
    async def test_change_password_revokes_all_sessions(self, handler, user_repo, token_repo, active_user):
        active_user.password_hash = _pw.hash("Secret123!")
        user_repo.get_by_id.return_value = active_user
        user_repo.save.return_value = active_user

        await handler.handle(ChangePasswordCommand(user_id=1, current_password="Secret123!", new_password="NewPass456!"))

        token_repo.revoke_all_for_user.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_raises(self, handler, user_repo, active_user):
        active_user.password_hash = _pw.hash("Secret123!")
        user_repo.get_by_id.return_value = active_user

        with pytest.raises(PasswordMismatchError):
            await handler.handle(ChangePasswordCommand(user_id=1, current_password="WrongPass!1", new_password="NewPass456!"))

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_does_not_update(self, handler, user_repo, token_repo, active_user):
        active_user.password_hash = _pw.hash("Secret123!")
        user_repo.get_by_id.return_value = active_user

        with pytest.raises(PasswordMismatchError):
            await handler.handle(ChangePasswordCommand(user_id=1, current_password="WrongPass!1", new_password="NewPass456!"))

        user_repo.save.assert_not_called()
        token_repo.revoke_all_for_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_change_password_user_not_found_raises(self, handler, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await handler.handle(ChangePasswordCommand(user_id=999, current_password="Secret123!", new_password="NewPass456!"))

    @pytest.mark.asyncio
    async def test_change_password_user_not_found_does_not_update(self, handler, user_repo, token_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await handler.handle(ChangePasswordCommand(user_id=999, current_password="Secret123!", new_password="NewPass456!"))

        user_repo.save.assert_not_called()
        token_repo.revoke_all_for_user.assert_not_called()


class TestEnable2FACommandHandler:
    @pytest.fixture
    def handler(self, user_repo, totp_service):
        return Enable2FACommandHandler(user_repo, totp_service)

    @pytest.mark.asyncio
    async def test_enable_2fa_success(self, handler, user_repo, totp_service, active_user):
        user_repo.get_by_id.return_value = active_user
        user_repo.save.return_value = active_user
        totp_service.generate_totp_secret.return_value = "BASE32SECRET"
        totp_service.get_totp_uri.return_value = "otpauth://totp/..."
        totp_service.generate_qr_code_base64.return_value = "base64qrstring"

        result = await handler.handle(Enable2FACommand(user_id=1))

        assert result.secret == "BASE32SECRET"
        assert result.qr_code_base64 == "base64qrstring"
        user_repo.save.assert_called_once()
        assert active_user.totp_secret == "BASE32SECRET"

    @pytest.mark.asyncio
    async def test_enable_2fa_already_enabled_raises(self, handler, user_repo, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa

        with pytest.raises(TwoFactorAlreadyEnabledError):
            await handler.handle(Enable2FACommand(user_id=1))

    @pytest.mark.asyncio
    async def test_enable_2fa_already_enabled_does_not_overwrite_secret(self, handler, user_repo, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa

        with pytest.raises(TwoFactorAlreadyEnabledError):
            await handler.handle(Enable2FACommand(user_id=1))

        user_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_enable_2fa_user_not_found_raises(self, handler, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await handler.handle(Enable2FACommand(user_id=999))


class TestConfirm2FACommandHandler:
    @pytest.fixture
    def handler(self, user_repo, totp_service):
        return Confirm2FACommandHandler(user_repo, totp_service)

    @pytest.mark.asyncio
    async def test_confirm_2fa_success(self, handler, user_repo, totp_service, active_user):
        active_user.totp_secret = "BASE32SECRET"
        user_repo.get_by_id.return_value = active_user
        user_repo.save.return_value = active_user
        totp_service.verify_totp.return_value = True

        await handler.handle(Confirm2FACommand(user_id=1, code="123456"))

        user_repo.save.assert_called_once()
        assert active_user.is_2fa_enabled is True

    @pytest.mark.asyncio
    async def test_confirm_2fa_invalid_code_raises(self, handler, user_repo, totp_service, active_user):
        active_user.totp_secret = "BASE32SECRET"
        user_repo.get_by_id.return_value = active_user
        totp_service.verify_totp.return_value = False

        with pytest.raises(InvalidTwoFactorCodeError):
            await handler.handle(Confirm2FACommand(user_id=1, code="000000"))

    @pytest.mark.asyncio
    async def test_confirm_2fa_invalid_code_does_not_enable(self, handler, user_repo, totp_service, active_user):
        active_user.totp_secret = "BASE32SECRET"
        user_repo.get_by_id.return_value = active_user
        totp_service.verify_totp.return_value = False

        with pytest.raises(InvalidTwoFactorCodeError):
            await handler.handle(Confirm2FACommand(user_id=1, code="000000"))

        user_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_confirm_2fa_no_secret_raises(self, handler, user_repo, active_user):
        active_user.totp_secret = None
        user_repo.get_by_id.return_value = active_user

        with pytest.raises(TwoFactorNotEnabledError):
            await handler.handle(Confirm2FACommand(user_id=1, code="123456"))


class TestDisable2FACommandHandler:
    @pytest.fixture
    def handler(self, user_repo, totp_service):
        return Disable2FACommandHandler(user_repo, totp_service)

    @pytest.mark.asyncio
    async def test_disable_2fa_success(self, handler, user_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        user_repo.save.return_value = user_with_2fa
        totp_service.verify_totp.return_value = True

        await handler.handle(Disable2FACommand(user_id=1, code="123456"))

        user_repo.save.assert_called_once()
        assert user_with_2fa.is_2fa_enabled is False
        assert user_with_2fa.totp_secret is None

    @pytest.mark.asyncio
    async def test_disable_2fa_invalid_code_raises(self, handler, user_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = False

        with pytest.raises(InvalidTwoFactorCodeError):
            await handler.handle(Disable2FACommand(user_id=1, code="000000"))

    @pytest.mark.asyncio
    async def test_disable_2fa_invalid_code_does_not_disable(self, handler, user_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = False

        with pytest.raises(InvalidTwoFactorCodeError):
            await handler.handle(Disable2FACommand(user_id=1, code="000000"))

        user_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_disable_2fa_not_enabled_raises(self, handler, user_repo, active_user):
        active_user.is_2fa_enabled = False
        active_user.totp_secret = None
        user_repo.get_by_id.return_value = active_user

        with pytest.raises(TwoFactorNotEnabledError):
            await handler.handle(Disable2FACommand(user_id=1, code="123456"))


class TestVerify2FAAndLoginCommandHandler:
    @pytest.fixture
    def handler(self, user_repo, token_repo, totp_service):
        return Verify2FAAndLoginCommandHandler(user_repo, token_repo, totp_service)

    @pytest.mark.asyncio
    async def test_verify_2fa_token_success(self, handler, user_repo, token_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = True
        token_repo.create.return_value = MagicMock()

        temp_token = TokenUtils.create_2fa_token(user_with_2fa.id, user_with_2fa.email)
        result = await handler.handle(Verify2FAAndLoginCommand(temp_token=temp_token, code="123456"))

        assert result.token_type == "bearer"
        assert result.access_token
        assert result.refresh_token is not None

    @pytest.mark.asyncio
    async def test_verify_2fa_wrong_code_raises(self, handler, user_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = False

        temp_token = TokenUtils.create_2fa_token(user_with_2fa.id, user_with_2fa.email)
        with pytest.raises(InvalidTwoFactorCodeError):
            await handler.handle(Verify2FAAndLoginCommand(temp_token=temp_token, code="000000"))

    @pytest.mark.asyncio
    async def test_verify_2fa_wrong_code_does_not_issue_tokens(self, handler, user_repo, token_repo, totp_service, user_with_2fa):
        user_repo.get_by_id.return_value = user_with_2fa
        totp_service.verify_totp.return_value = False

        temp_token = TokenUtils.create_2fa_token(user_with_2fa.id, user_with_2fa.email)
        with pytest.raises(InvalidTwoFactorCodeError):
            await handler.handle(Verify2FAAndLoginCommand(temp_token=temp_token, code="000000"))

        token_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_2fa_invalid_temp_token_raises(self, handler):
        with pytest.raises(InvalidTokenError):
            await handler.handle(Verify2FAAndLoginCommand(temp_token="garbage.token.here", code="123456"))

    @pytest.mark.asyncio
    async def test_verify_2fa_access_token_as_temp_raises(self, handler, user_repo, active_user):
        user_repo.get_by_id.return_value = active_user
        access_token = TokenUtils.create_access_token(active_user.id, active_user.email)

        with pytest.raises(InvalidTokenError):
            await handler.handle(Verify2FAAndLoginCommand(temp_token=access_token, code="123456"))


class TestVerifyEmailCommandHandler:
    @pytest.fixture
    def handler(self, user_repo, mail_service):
        return VerifyEmailCommandHandler(user_repo, mail_service)

    @pytest.mark.asyncio
    async def test_verify_email_success(self, handler, user_repo, mail_service, active_user):
        active_user.is_verified = False
        user_repo.get_by_id.return_value = active_user
        user_repo.save.return_value = active_user
        mail_service.decode_email_token.return_value = {"sub": "1"}

        await handler.handle(VerifyEmailCommand(token="valid_token"))

        user_repo.save.assert_called_once()
        assert active_user.is_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_already_verified_raises(self, handler, user_repo, mail_service, active_user):
        active_user.is_verified = True
        user_repo.get_by_id.return_value = active_user
        mail_service.decode_email_token.return_value = {"sub": "1"}

        with pytest.raises(EmailAlreadyVerifiedError):
            await handler.handle(VerifyEmailCommand(token="valid_token"))

    @pytest.mark.asyncio
    async def test_verify_email_already_verified_does_not_re_verify(self, handler, user_repo, mail_service, active_user):
        active_user.is_verified = True
        user_repo.get_by_id.return_value = active_user
        mail_service.decode_email_token.return_value = {"sub": "1"}

        with pytest.raises(EmailAlreadyVerifiedError):
            await handler.handle(VerifyEmailCommand(token="valid_token"))

        user_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found_raises(self, handler, user_repo, mail_service):
        user_repo.get_by_id.return_value = None
        mail_service.decode_email_token.return_value = {"sub": "999"}

        with pytest.raises(UserNotFoundError):
            await handler.handle(VerifyEmailCommand(token="valid_token"))

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token_raises(self, handler, mail_service):
        mail_service.decode_email_token.side_effect = InvalidTokenError("bad token")

        with pytest.raises(InvalidTokenError):
            await handler.handle(VerifyEmailCommand(token="bad_token"))