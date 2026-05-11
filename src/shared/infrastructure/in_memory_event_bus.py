import asyncio
import logging
from collections.abc import Callable
from typing import Any

from src.shared.infrastructure.event_bus_interface import EventHandler, IEventBus

logger = logging.getLogger(__name__)


class InMemoryEventBus(IEventBus):
    def __init__(self) -> None:
        self._subscribers: dict[type, list[EventHandler]] = {}

    def subscribe(self, event_type: type) -> Callable[[EventHandler], EventHandler]:
        def decorator(handler: EventHandler) -> EventHandler:
            self._subscribers.setdefault(event_type, []).append(handler)
            logger.debug("Registered handler %s for %s", handler.__name__, event_type.__name__)
            return handler

        return decorator

    async def publish(self, event: Any) -> None:
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])

        if not handlers:
            logger.debug("No handlers registered for %s — skipping", event_type.__name__)
            return

        tasks = [asyncio.create_task(h(event)) for h in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.exception(
                    "Handler failed for event %s: %s",
                    event_type.__name__,
                    result,
                )
