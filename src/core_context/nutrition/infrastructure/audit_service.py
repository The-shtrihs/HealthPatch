import json
import logging
from typing import Any

from src.core_context.nutrition.application.audit_service import INutritionAuditService

logger = logging.getLogger("audit.nutrition")


class LoggingNutritionAuditService(INutritionAuditService):
    """Logs nutrition-domain audit records to the standard logger.

    Basic implementation of INutritionAuditService. Replacing it with a
    persistent store (DB table, S3, etc.) does not require changes to any
    command handler — they depend only on the abstract contract.
    """

    async def record(self, event: Any) -> None:
        event_type = type(event).__name__
        payload = _serialize(event)
        logger.info("AUDIT nutrition | %s | %s", event_type, payload)


def _serialize(event: Any) -> str:
    if hasattr(event, "__dataclass_fields__"):
        data = {f: getattr(event, f) for f in event.__dataclass_fields__}
        return json.dumps(data, default=str)
    return str(event)
