import asyncio
import logging
import pickle
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from redis.asyncio import Redis

from src.shared.infrastructure.event_bus_interface import IEventBus

logger = logging.getLogger(__name__)

EventHandler = Callable[[Any], Awaitable[None]]
DispatchMode = Literal["local", "redis"]


class HybridEventBus(IEventBus):
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client
        self._local_subscribers: dict[type, list[EventHandler]] = {}
        self._redis_subscribers: dict[str, list[EventHandler]] = {}

        self._pubsub = self._redis.pubsub()
        self._listener_task: asyncio.Task | None = None

    def subscribe(self, event_type: type, mode: DispatchMode = "local") -> Callable[[EventHandler], EventHandler]:
        def decorator(handler: EventHandler) -> EventHandler:
            if mode == "local":
                self._local_subscribers.setdefault(event_type, []).append(handler)
                logger.debug("Registered LOCAL handler %s for %s", handler.__name__, event_type.__name__)
            elif mode == "redis":
                channel_name = event_type.__name__
                self._redis_subscribers.setdefault(channel_name, []).append(handler)
                logger.debug("Registered REDIS handler %s for %s", handler.__name__, channel_name)
            return handler

        return decorator

    async def publish(self, event: Any) -> None:
        event_type = type(event)
        local_handlers = self._local_subscribers.get(event_type, [])
        if local_handlers:
            tasks = [asyncio.create_task(h(event)) for h in local_handlers]
            asyncio.create_task(self._gather_and_log(tasks, f"LOCAL:{event_type.__name__}"))

        channel_name = event_type.__name__
        if channel_name in self._redis_subscribers:
            serialized_event = pickle.dumps(event)
            await self._redis.publish(channel_name, serialized_event)
            logger.debug("Published event %s to Redis channel", channel_name)

    async def start(self) -> None:
        if not self._redis_subscribers:
            logger.info("No Redis subscribers registered. Redis listener not started.")
            return
        channels = list(self._redis_subscribers.keys())
        await self._pubsub.subscribe(*channels)

        self._listener_task = asyncio.create_task(self._listen())
        logger.info("HybridEventBus Redis listener started for channels: %s", channels)

    async def stop(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        try:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
        except Exception as e:
            logger.error("Error closing Redis pubsub: %s", e)

        logger.info("HybridEventBus listener stopped.")

    async def _listen(self) -> None:
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    channel_name = message["channel"].decode("utf-8")
                    try:
                        event = pickle.loads(message["data"])
                    except Exception as e:
                        logger.error("Failed to unpickle event from channel %s: %s", channel_name, e)
                        continue

                    handlers = self._redis_subscribers.get(channel_name, [])
                    if not handlers:
                        continue

                    tasks = [asyncio.create_task(h(event)) for h in handlers]
                    asyncio.create_task(self._gather_and_log(tasks, f"REDIS:{channel_name}"))

        except asyncio.CancelledError:
            logger.debug("Redis listener loop was cancelled.")
        except Exception as e:
            logger.exception("Redis listener encountered an unexpected error: %s", e)

    async def _gather_and_log(self, tasks: list[asyncio.Task], event_name: str):
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.exception("Handler failed for event [%s]: %s", event_name, result)
