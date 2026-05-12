import json
import logging
from typing import Any

from src.shared.infrastructure.notify_service import NotifyService

logger = logging.getLogger(__name__)


class LoggingNotifyService(NotifyService):
    """
    Logs domain events to Python logger.
    
    Use this implementation for development/testing.
    Later: swap to push notification provider (FCM, APNs, email, SMS, etc.)
    without changing event handlers.
    """

    async def notify(self, event: Any) -> None:
        """Log the event with its type and data."""
        event_type = type(event).__name__

        if hasattr(event, "__dataclass_fields__"):
            event_data = {
                field: getattr(event, field)
                for field in event.__dataclass_fields__
            }
            event_data_str = json.dumps(
                event_data,
                default=str,
                indent=2,
            )
        else:
            event_data_str = str(event)
        
        logger.info(
            "📬 Event: %s\n%s",
            event_type,
            event_data_str,
        )
