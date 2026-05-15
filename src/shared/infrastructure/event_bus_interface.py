import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Literal

logger = logging.getLogger(__name__)

EventHandler = Callable[[Any], Awaitable[None]]
DeliveryMode = Literal["sync", "async"]


class IEventBus(ABC):
    @abstractmethod
    def subscribe(
        self,
        event_type: type,
        mode: DeliveryMode = "sync",
        task_name: str | None = None,
    ) -> Callable[[EventHandler], EventHandler]: ...

    @abstractmethod
    async def publish(self, event: Any) -> None: ...
