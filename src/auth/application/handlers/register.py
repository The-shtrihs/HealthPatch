from src.auth.application.commands import RegisterCommand
from src.auth.application.token_utils import PasswordUtils
from src.auth.domain.events import UserRegisteredEvent
from src.auth.domain.factory import UserFactory
from src.auth.domain.interfaces import IUserRepository
from src.shared.infrastructure.event_bus_interface import IEventBus


class RegisterCommandHandler:
    def __init__(
        self,
        user_repo: IUserRepository,
        password_utils: PasswordUtils,
        event_bus: IEventBus,
    ):
        self._user_repo = user_repo
        self._pw = password_utils
        self._event_bus = event_bus
        self._factory = UserFactory(user_repo)

    async def handle(self, cmd: RegisterCommand) -> None:
        user = await self._factory.create_regular(
            name=cmd.name,
            email=cmd.email,
            password_hash=self._pw.hash(cmd.password),
        )
        saved = await self._user_repo.create(
            name=user.name,
            email=user.email,
            password_hash=user.password_hash,
        )
        await self._event_bus.publish(UserRegisteredEvent(user_id=saved.id, email=saved.email, name=saved.name))
