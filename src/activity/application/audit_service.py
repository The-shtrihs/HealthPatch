from abc import ABC, abstractmethod
from typing import Any


class IActivityAuditService(ABC):
    """Contract for the activity-domain audit service.

    Persists an audit trail of training-related business actions: workouts
    started/ended, plans created/published/deleted, personal records beaten,
    etc. Used by handlers (sync) and by event subscribers (async) so the same
    audit fact can be produced through both communication styles.
    """

    @abstractmethod
    async def record(self, event: Any) -> None: ...
