import logging

from src.core_context.auth.application.audit_service import IAuthAuditService
from src.core_context.auth.application.commands import RegisterCommand
from src.core_context.auth.application.token_utils import PasswordUtils
from src.core_context.auth.domain.events import UserRegisteredEvent
from src.core_context.auth.domain.factory import UserFactory
from src.core_context.auth.domain.interfaces import IUserRepository
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


class RegisterCommandHandler:
    def __init__(
        self,
        user_repo: IUserRepository,
        password_utils: PasswordUtils,
        event_bus: IEventBus,
        audit_service: IAuthAuditService,
    ):
        self._user_repo = user_repo
        self._pw = password_utils
        self._event_bus = event_bus
        self._audit_service = audit_service
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
        registered_event = UserRegisteredEvent(user_id=saved.id, email=saved.email, name=saved.name)

        # Synchronous audit: direct interface call in the same execution thread.
        # Audit is an auxiliary side-operation; if it fails we log and continue
        # rather than rolling back the registration — losing one audit record
        # is far less bad than refusing a successful sign-up.
        try:
            await self._audit_service.record(registered_event)
        except Exception:
            logger.exception("Audit recording failed for UserRegisteredEvent user_id=%s", saved.id)

        await self._event_bus.publish(registered_event)
