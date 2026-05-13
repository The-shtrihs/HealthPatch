from abc import ABC, abstractmethod
from typing import Any


class INotifyService(ABC):
    """
    Abstract base for notification services.

    Implementations can:
    - Log events to stdout/logger (logging adapter)
    - Send push notifications via FCM, APNs, etc.
    - Send emails or SMS
    - Store notification records in DB

    This design allows swapping implementations at runtime without changing callers.
    """

    @abstractmethod
    def notify(self, event: Any) -> None: ...