import logging
from typing import Any

from src.shared.infrastructure.base_uow import BaseUnitOfWork
from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)


async def dispatch_domain_events(uow: BaseUnitOfWork, bus: IEventBus) -> None:
    events: list[Any] = list(uow.events)
    uow.events.clear()

    for event in events:
        logger.debug("Dispatching %s", type(event).__name__)
        await bus.publish(event)