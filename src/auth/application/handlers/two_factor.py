from src.auth.application.commands import (
    Confirm2FACommand, Disable2FACommand,
    Enable2FACommand, Verify2FAAndLoginCommand,
)
from src.auth.application.read_models import TokenReadModel, TwoFactorSetupReadModel
from src.auth.application.token_utils import TokenUtils, issue_refresh_token
from src.auth.domain.errors import (
    InvalidTwoFactorCodeError, TwoFactorNotEnabledError, UserNotFoundError,
)
from src.auth.domain.interfaces import IRefreshTokenRepository, ITotpService, IUserRepository
from src.core.config import get_settings
from src.core.constants import SECONDS_PER_MINUTE


class Enable2FACommandHandler:
    def __init__(self, user_repo: IUserRepository, totp_service: ITotpService):
        self._user_repo = user_repo
        self._totp = totp_service

    async def handle(self, cmd: Enable2FACommand) -> TwoFactorSetupReadModel:
        user = await self._user_repo.get_by_id(cmd.user_id)
        if not user:
            raise UserNotFoundError(cmd.user_id)
        secret = self._totp.generate_totp_secret()
        user.initiate_2fa(secret)
        await self._user_repo.save(user)
        uri = self._totp.get_totp_uri(secret, user_email=user.email)
        return TwoFactorSetupReadModel(
            secret=secret,
            qr_code_base64=self._totp.generate_qr_code_base64(uri),
        )


class Confirm2FACommandHandler:
    def __init__(self, user_repo: IUserRepository, totp_service: ITotpService):
        self._user_repo = user_repo
        self._totp = totp_service

    async def handle(self, cmd: Confirm2FACommand) -> None:
        user = await self._user_repo.get_by_id(cmd.user_id)
        if not user:
            raise UserNotFoundError(cmd.user_id)
        if not user.totp_secret:
            raise TwoFactorNotEnabledError("Cannot confirm 2FA setup because it was not initiated")
        if not self._totp.verify_totp(cmd.code, user.totp_secret):
            raise InvalidTwoFactorCodeError()
        user.confirm_2fa()
        await self._user_repo.save(user)


class Disable2FACommandHandler:
    def __init__(self, user_repo: IUserRepository, totp_service: ITotpService):
        self._user_repo = user_repo
        self._totp = totp_service

    async def handle(self, cmd: Disable2FACommand) -> None:
        user = await self._user_repo.get_by_id(cmd.user_id)
        if not user:
            raise UserNotFoundError(cmd.user_id)
        if not user.is_2fa_enabled or not user.totp_secret:
            raise TwoFactorNotEnabledError()
        if not self._totp.verify_totp(cmd.code, user.totp_secret):
            raise InvalidTwoFactorCodeError()
        user.disable_2fa()
        await self._user_repo.save(user)


class Verify2FAAndLoginCommandHandler:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: IRefreshTokenRepository,
        totp_service: ITotpService,
    ):
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._totp = totp_service
        self._settings = get_settings()

    async def handle(self, cmd: Verify2FAAndLoginCommand) -> TokenReadModel:
        payload = TokenUtils.decode_2fa_token(cmd.temp_token)
        user = await self._user_repo.get_by_id(int(payload["sub"]))
        if not user:
            raise UserNotFoundError()
        if not user.is_2fa_enabled or not user.totp_secret:
            raise TwoFactorNotEnabledError()
        if not self._totp.verify_totp(cmd.code, user.totp_secret):
            raise InvalidTwoFactorCodeError()
        refresh_token = await issue_refresh_token(self._token_repo, user.id, cmd.device_info)
        return TokenReadModel(
            access_token=TokenUtils.create_access_token(user.id, user.email),
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self._settings.access_token_expire_minutes * SECONDS_PER_MINUTE,
        )