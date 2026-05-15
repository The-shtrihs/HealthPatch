import asyncio
import logging
from collections.abc import Callable
from typing import Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from pydantic import BaseModel

from src.shared.infrastructure.event_bus_interface import DeliveryMode, EventHandler, IEventBus

logger = logging.getLogger(__name__)


class EventBus(IEventBus):
    def __init__(self) -> None:
        self._sync_subscribers: dict[type, list[EventHandler]] = {}
        self._async_task_names: dict[type, list[str]] = {}
        self.arq_pool: ArqRedis | None = None

    async def start_arq(self, redis_url: str) -> None:
        self.arq_pool = await create_pool(RedisSettings.from_dsn(redis_url))

    async def stop_arq(self) -> None:
        if self.arq_pool:
            await self.arq_pool.close()

    def subscribe(
        self,
        event_type: type,
        mode: DeliveryMode = "sync",
        task_name: str | None = None,
    ) -> Callable[[EventHandler], EventHandler]:
        def decorator(handler: EventHandler) -> EventHandler:
            if mode == "sync":
                self._sync_subscribers.setdefault(event_type, []).append(handler)
            else:
                name = task_name or handler.__name__
                self._async_task_names.setdefault(event_type, []).append(name)
            return handler

        return decorator

    async def publish(self, event: Any) -> None:
        event_type = type(event)

        sync_handlers = self._sync_subscribers.get(event_type, [])
        if sync_handlers:
            await asyncio.gather(*(h(event) for h in sync_handlers), return_exceptions=False)

        async_tasks = self._async_task_names.get(event_type, [])
        if async_tasks:
            if self.arq_pool is None:
                logger.warning("Async handlers registered for %s but arq pool is not initialized; skipping", event_type.__name__)
                return
            payload = self._serialize(event)
            for task_name in async_tasks:
                await self.arq_pool.enqueue_job(task_name, payload)

    @staticmethod
    def _serialize(event: Any) -> dict[str, Any]:
        if isinstance(event, BaseModel):
            return event.model_dump(mode="json")
        if hasattr(event, "__dict__"):
            return dict(event.__dict__)
        raise TypeError(f"Cannot serialize event of type {type(event).__name__} for async dispatch")
