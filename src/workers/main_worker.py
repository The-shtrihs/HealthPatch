import logging
from typing import Any

from arq.connections import RedisSettings

from src.core.config import get_settings
from src.shared.infrastructure.mail import MailService

logger = logging.getLogger(__name__)
settings = get_settings()


async def startup(ctx: dict[str, Any]) -> None:
    logger.info("Starting worker, initializing resources...")

    ctx["mail_service"] = MailService()

    logger.info("MailService initialized.")


async def task_send_verification_email(ctx: dict[str, Any], user_id: int, user_email: str, name: str) -> None:
    mail_service: MailService = ctx["mail_service"]
    logger.info("Sending verification email to %s...", user_email)
    await mail_service.send_verification_email(user_id=user_id, user_email=user_email, name=name)
    logger.info("Verification email sent to %s successfully.", user_email)


async def task_send_password_reset_email(ctx: dict[str, Any], user_id: int, user_email: str, name: str) -> None:
    mail_service: MailService = ctx["mail_service"]

    logger.info("Sending password reset email to %s...", user_email)
    await mail_service.send_password_reset_email(user_id=user_id, user_email=user_email, name=name)
    logger.info("Password reset email sent to %s successfully.", user_email)


async def task_send_generic_email(ctx: dict[str, Any], to_email: str, subject: str, template_name: str, template_body: dict) -> None:
    mail_service: MailService = ctx["mail_service"]

    logger.info("Sending generic email '%s' to %s...", subject, to_email)
    await mail_service.send_email(to_email, subject, template_name, template_body)


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    on_startup = startup

    functions = [task_send_verification_email, task_send_password_reset_email, task_send_generic_email]

    max_tries = 3
