from src.auth.application.commands import ForgotPasswordCommand, ResetPasswordCommand
from src.auth.application.token_utils import PasswordUtils
from src.auth.domain.errors import UserNotFoundError
from src.auth.domain.events import PasswordResetRequestedEvent
from src.auth.domain.interfaces import IMailService, IRefreshTokenRepository, IUserRepository
from src.shared.infrastructure.event_bus_interface import IEventBus


class ForgotPasswordCommandHandler:
    def __init__(self, user_repo: IUserRepository, event_bus: IEventBus):
        self._user_repo = user_repo
        self._event_bus = event_bus 

    async def handle(self, cmd: ForgotPasswordCommand) -> None:
        user = await self._user_repo.get_by_email(cmd.email)
        if user:
            await self._event_bus.publish(
                PasswordResetRequestedEvent(user_id=user.id, email=user.email, name=user.name)
            )
class ResetPasswordCommandHandler:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: IRefreshTokenRepository,
        mail_service: IMailService,
        password_utils: PasswordUtils,
    ):
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._mail = mail_service
        self._pw = password_utils

    async def handle(self, cmd: ResetPasswordCommand) -> None:
        payload = self._mail.decode_email_token(cmd.token, expected_purpose="password_reset")
        user = await self._user_repo.get_by_id(int(payload["sub"]))
        if not user:
            raise UserNotFoundError()
        user.change_password(self._pw.hash(cmd.new_password))
        await self._user_repo.save(user)
        await self._token_repo.revoke_all_for_user(user.id)
