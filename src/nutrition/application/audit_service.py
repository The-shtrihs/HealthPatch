from abc import ABC, abstractmethod
from typing import Any


class INutritionAuditService(ABC):
    """Contract for the nutrition-domain audit service.

    Records diary-changing actions (meal entries added/updated/deleted, diary
    notes/water updated) for later audit/analytics. Implementations are kept
    behind this interface so command handlers do not depend on storage details.
    """

    @abstractmethod
    async def record(self, event: Any) -> None: ...
