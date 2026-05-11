import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)

EventHandler = Callable[[Any], Awaitable[None]]


class IEventBus(ABC):

    @abstractmethod
    def subscribe(self, event_type: type) -> Callable[[EventHandler], EventHandler]: ...


    @abstractmethod
    async def publish(self, event: Any) -> None: ...
