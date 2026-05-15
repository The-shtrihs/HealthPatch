import json
import logging
from typing import Any

from src.core_context.activity.application.audit_service import IActivityAuditService

logger = logging.getLogger("audit.activity")


class LoggingActivityAuditService(IActivityAuditService):
    """Logs activity-domain audit records to the standard logger.

    Acts as the basic implementation behind IActivityAuditService. Future
    implementations could persist records to an audit table or stream them to
    a centralized log aggregator; callers do not need to change.
    """

    async def record(self, event: Any) -> None:
        event_type = type(event).__name__
        payload = _serialize(event)
        logger.info("AUDIT activity | %s | %s", event_type, payload)


def _serialize(event: Any) -> str:
    if hasattr(event, "__dataclass_fields__"):
        data = {f: getattr(event, f) for f in event.__dataclass_fields__}
        return json.dumps(data, default=str)
    return str(event)
