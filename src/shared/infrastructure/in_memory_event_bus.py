import asyncio
import logging
from collections.abc import Callable
from typing import Any

from src.shared.infrastructure.event_bus_interface import DeliveryMode, EventHandler, IEventBus

logger = logging.getLogger(__name__)


class InMemoryEventBus(IEventBus):
    def __init__(self) -> None:
        self._subscribers: dict[type, list[EventHandler]] = {}

    def subscribe(
        self,
        event_type: type,
        mode: DeliveryMode = "sync",
        task_name: str | None = None,
    ) -> Callable[[EventHandler], EventHandler]:
        del mode, task_name

        def decorator(handler: EventHandler) -> EventHandler:
            self._subscribers.setdefault(event_type, []).append(handler)
            return handler

        return decorator

    async def publish(self, event: Any) -> None:
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])

        if not handlers:
            return

        tasks = [asyncio.create_task(h(event)) for h in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.exception("Handler failed for event %s: %s", event_type.__name__, result)
