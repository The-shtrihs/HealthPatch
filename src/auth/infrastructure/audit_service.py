import json
import logging
from typing import Any

from src.auth.application.audit_service import IAuthAuditService

logger = logging.getLogger("audit.auth")


class LoggingAuthAuditService(IAuthAuditService):
    """Audit-trail writer that logs structured records to the standard logger.

    For now this is a basic implementation suitable for development and the
    MVP. The interface is the production contract — when persistence is
    required we can swap in an implementation that writes to an append-only
    table or to an external SIEM without touching any handler.
    """

    async def record(self, event: Any) -> None:
        event_type = type(event).__name__
        payload = _serialize(event)
        logger.info("AUDIT auth | %s | %s", event_type, payload)


def _serialize(event: Any) -> str:
    if hasattr(event, "__dataclass_fields__"):
        data = {f: getattr(event, f) for f in event.__dataclass_fields__}
        return json.dumps(data, default=str)
    return str(event)
