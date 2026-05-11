import asyncio
import logging
import pickle
from collections.abc import Awaitable, Callable
from typing import Any

from redis.asyncio import Redis

from src.shared.infrastructure.event_bus_interface import EventHandler, IEventBus 

logger = logging.getLogger(__name__)


class RedisEventBus(IEventBus):
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client
        self._subscribers: dict[str, list[EventHandler]] = {}
        self._pubsub = self._redis.pubsub()
        self._listener_task: asyncio.Task | None = None

    def subscribe(self, event_type: type) -> Callable[[EventHandler], EventHandler]:
        def decorator(handler: EventHandler) -> EventHandler:
            channel_name = event_type.__name__
            self._subscribers.setdefault(channel_name, []).append(handler)
            logger.debug("Registered Redis handler %s for %s", handler.__name__, channel_name)
            return handler
        return decorator

    async def publish(self, event: Any) -> None:
        channel_name = type(event).__name__
        
        serialized_event = pickle.dumps(event)
        
        await self._redis.publish(channel_name, serialized_event)
        logger.debug("Published event %s to Redis channel", channel_name)

    async def start(self) -> None:
        if not self._subscribers:
            logger.info("No event subscribers registered. Redis listener not started.")
            return

        channels = list(self._subscribers.keys())
        await self._pubsub.subscribe(*channels)
        
        self._listener_task = asyncio.create_task(self._listen())
        logger.info("RedisEventBus listener started for channels: %s", channels)

    async def stop(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
        await self._pubsub.unsubscribe()
        await self._pubsub.close()
        logger.info("RedisEventBus listener stopped.")

    async def _listen(self) -> None:
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    channel_name = message["channel"].decode("utf-8")
                    
                    event = pickle.loads(message["data"])
                    
                    handlers = self._subscribers.get(channel_name, [])
                    
                    if not handlers:
                        continue

                    tasks = [asyncio.create_task(h(event)) for h in handlers]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for result in results:
                        if isinstance(result, Exception):
                            logger.exception(
                                "Handler failed for event %s: %s",
                                channel_name,
                                result,
                            )
        except asyncio.CancelledError:
            pass 