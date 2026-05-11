# src/auth/application/event_handlers.py
from src.shared.infrastructure.event_bus_interface import IEventBus
from src.auth.domain.events import (
    UserRegisteredEvent, PasswordResetRequestedEvent, VerificationEmailRequestedEvent
)

def register_auth_event_handlers(event_bus: IEventBus):

    @event_bus.subscribe(UserRegisteredEvent)
    async def on_user_registered(event: UserRegisteredEvent):
        if hasattr(event_bus, 'arq_pool') and event_bus.arq_pool:
            await event_bus.arq_pool.enqueue_job(
                'task_send_verification_email', 
                event.user_id, event.email, event.name
            )

    @event_bus.subscribe(VerificationEmailRequestedEvent)
    async def on_verification_requested(event: VerificationEmailRequestedEvent):
        if hasattr(event_bus, 'arq_pool') and event_bus.arq_pool:
            await event_bus.arq_pool.enqueue_job(
                'task_send_verification_email', 
                event.user_id, event.email, event.name
            )

    @event_bus.subscribe(PasswordResetRequestedEvent)
    async def on_password_reset_requested(event: PasswordResetRequestedEvent):
        if hasattr(event_bus, 'arq_pool') and event_bus.arq_pool:
            await event_bus.arq_pool.enqueue_job(
                'task_send_password_reset_email', 
                event.user_id, event.email, event.name
            )