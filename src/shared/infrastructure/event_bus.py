import asyncio
import logging
from collections.abc import Callable
from typing import Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from src.shared.infrastructure.event_bus_interface import IEventBus, EventHandler

logger = logging.getLogger(__name__)


class EventBus(IEventBus):
    def __init__(self) -> None:
        self._local_subscribers: dict[type, list[EventHandler]] = {}
        self.arq_pool: ArqRedis | None = None

    async def start_arq(self, redis_url: str) -> None:
        self.arq_pool = await create_pool(
            RedisSettings.from_dsn(redis_url)
        )
        logger.info("ARQ pool initialized successfully.")

    async def stop_arq(self) -> None:
        if self.arq_pool:
            await self.arq_pool.close()
            logger.info("ARQ pool closed.")

    def subscribe(self, event_type: type) -> Callable[[EventHandler], EventHandler]:
        def decorator(handler: EventHandler) -> EventHandler:
            self._local_subscribers.setdefault(event_type, []).append(handler)
            logger.debug("Registered local handler %s for %s", handler.__name__, event_type.__name__)
            return handler
        return decorator

    async def publish(self, event: Any) -> None:
        event_type = type(event)
        local_handlers = self._local_subscribers.get(event_type, [])
        
        if not local_handlers:
            return

        tasks = [asyncio.create_task(h(event)) for h in local_handlers]
        asyncio.create_task(self._gather_and_log(tasks, event_type.__name__))

    async def _gather_and_log(self, tasks: list[asyncio.Task], event_name: str) -> None:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.exception("Handler failed for event %s: %s", event_name, result)