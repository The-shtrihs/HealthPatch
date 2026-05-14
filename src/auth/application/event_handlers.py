from src.auth.application.audit_service import IAuthAuditService
from src.auth.domain.events import PasswordResetRequestedEvent, UserRegisteredEvent, VerificationEmailRequestedEvent
from src.shared.infrastructure.event_bus_interface import IEventBus


def register_auth_event_handlers(event_bus: IEventBus, audit_service: IAuthAuditService) -> None:
    """Asynchronous audit path for the auth domain.

    Subscribes the audit service to immutable past-tense events emitted by
    auth command handlers. The audit-trail write happens independently of the
    enqueued email job — neither blocks the other.
    """

    @event_bus.subscribe(UserRegisteredEvent)
    async def on_user_registered(event: UserRegisteredEvent):
        await audit_service.record(event)
        if hasattr(event_bus, "arq_pool") and event_bus.arq_pool:
            await event_bus.arq_pool.enqueue_job("task_send_verification_email", event.user_id, event.email, event.name)

    @event_bus.subscribe(VerificationEmailRequestedEvent)
    async def on_verification_requested(event: VerificationEmailRequestedEvent):
        await audit_service.record(event)
        if hasattr(event_bus, "arq_pool") and event_bus.arq_pool:
            await event_bus.arq_pool.enqueue_job("task_send_verification_email", event.user_id, event.email, event.name)

    @event_bus.subscribe(PasswordResetRequestedEvent)
    async def on_password_reset_requested(event: PasswordResetRequestedEvent):
        await audit_service.record(event)
        if hasattr(event_bus, "arq_pool") and event_bus.arq_pool:
            await event_bus.arq_pool.enqueue_job("task_send_password_reset_email", event.user_id, event.email, event.name)
