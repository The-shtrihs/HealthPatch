import logging
from typing import Any

from arq.connections import RedisSettings

import src.models  # noqa: F401  registers every ORM class with the SQLAlchemy mapper
from src.analytics_context.audit.application import handlers as audit_handlers
from src.analytics_context.projections.activity_history import handlers as activity_history_handlers
from src.core.config import get_settings
from src.core.database import async_session_factory
from src.shared.infrastructure.mail import MailService

logger = logging.getLogger(__name__)
settings = get_settings()


async def startup(ctx: dict[str, Any]) -> None:
    ctx["mail_service"] = MailService()
    audit_handlers.configure(async_session_factory)
    activity_history_handlers.configure(async_session_factory)


async def task_send_verification_email(ctx: dict[str, Any], user_id: int, user_email: str, name: str) -> None:
    mail_service: MailService = ctx["mail_service"]
    await mail_service.send_verification_email(user_id=user_id, user_email=user_email, name=name)


async def task_send_password_reset_email(ctx: dict[str, Any], user_id: int, user_email: str, name: str) -> None:
    mail_service: MailService = ctx["mail_service"]
    await mail_service.send_password_reset_email(user_id=user_id, user_email=user_email, name=name)


async def task_send_generic_email(ctx: dict[str, Any], to_email: str, subject: str, template_name: str, template_body: dict) -> None:
    mail_service: MailService = ctx["mail_service"]
    await mail_service.send_email(to_email, subject, template_name, template_body)


def _make_arq_adapter(coro):
    async def _adapter(ctx: dict[str, Any], payload: dict[str, Any]) -> None:
        del ctx
        await coro(payload)

    _adapter.__name__ = coro.__name__
    return _adapter


_AUDIT_TASKS = [_make_arq_adapter(fn) for _, _, fn in audit_handlers.ASYNC_AUDIT_HANDLERS]
_PROJECTION_TASKS = [_make_arq_adapter(fn) for _, _, fn in activity_history_handlers.PROJECTION_HANDLERS]


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(str(settings.redis_url))

    on_startup = startup

    functions = [
        task_send_verification_email,
        task_send_password_reset_email,
        task_send_generic_email,
        *_AUDIT_TASKS,
        *_PROJECTION_TASKS,
    ]

    max_tries = 3
