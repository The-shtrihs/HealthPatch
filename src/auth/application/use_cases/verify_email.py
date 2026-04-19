from src.auth.domain.errors import UserNotFoundError
from src.auth.domain.interfaces import IMailService, IUserRepository


class VerifyEmailUseCase:
    def __init__(self, user_repo: IUserRepository, mail_service: IMailService):
        self._user_repo = user_repo
        self._mail = mail_service

    async def execute(self, token: str) -> None:
        payload = self._mail.decode_email_token(token, expected_purpose="email_verify")
        user = await self._user_repo.get_by_id(int(payload["sub"]))
        if not user:
            raise UserNotFoundError()
        user.verify_email()
        await self._user_repo.save(user)


class ResendVerificationUseCase:
    def __init__(self, user_repo: IUserRepository, mail_service: IMailService):
        self._user_repo = user_repo
        self._mail = mail_service

    async def execute(self, email: str, background_tasks) -> None:
        user = await self._user_repo.get_by_email(email)
        if user and not user.is_verified:
            background_tasks.add_task(
                self._mail.send_verification_email,
                user_id=user.id,
                user_email=user.email,
                name=user.name,
            )
