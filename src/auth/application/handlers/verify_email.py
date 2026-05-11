from src.auth.application.commands import ResendVerificationCommand, VerifyEmailCommand
from src.auth.domain.errors import UserNotFoundError
from src.auth.domain.events import VerificationEmailRequestedEvent
from src.auth.domain.interfaces import IMailService, IUserRepository
from src.shared.infrastructure.event_bus_interface import IEventBus


class VerifyEmailCommandHandler:
    def __init__(self, user_repo: IUserRepository, mail_service: IMailService):
        self._user_repo = user_repo
        self._mail = mail_service

    async def handle(self, cmd: VerifyEmailCommand) -> None:
        payload = self._mail.decode_email_token(cmd.token, expected_purpose="email_verify")
        user = await self._user_repo.get_by_id(int(payload["sub"]))
        if not user:
            raise UserNotFoundError()
        user.verify_email()
        await self._user_repo.save(user)


class ResendVerificationCommandHandler:
    def __init__(self, user_repo: IUserRepository, event_bus: IEventBus):
        self._user_repo = user_repo
        self._event_bus = event_bus 

    async def handle(self, cmd: ResendVerificationCommand) -> None:
        user = await self._user_repo.get_by_email(cmd.email)
        if user and not user.is_verified:
            await self._event_bus.publish(
                VerificationEmailRequestedEvent(user_id=user.id, email=user.email, name=user.name)
            )
