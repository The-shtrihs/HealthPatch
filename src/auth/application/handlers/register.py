from fastapi import BackgroundTasks

from src.auth.application.commands import RegisterCommand
from src.auth.application.token_utils import PasswordUtils
from src.auth.domain.factory import UserFactory
from src.auth.domain.interfaces import IMailService, IUserRepository


class RegisterCommandHandler:
    def __init__(
        self,
        user_repo: IUserRepository,
        mail_service: IMailService,
        password_utils: PasswordUtils,
    ):
        self._user_repo = user_repo
        self._mail = mail_service
        self._pw = password_utils
        self._factory = UserFactory(user_repo)

    async def handle(self, cmd: RegisterCommand, background_tasks: BackgroundTasks) -> None:
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
        background_tasks.add_task(
            self._mail.send_verification_email,
            user_id=saved.id,
            user_email=saved.email,
            name=saved.name,
        )