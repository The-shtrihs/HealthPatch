from abc import ABC, abstractmethod
from typing import Any


class IAuthAuditService(ABC):
    """Contract for the auth-domain audit service.

    Records security-relevant facts (registrations, password resets, verification
    re-sends, etc.) so that they can be inspected later. The interface is
    technology-agnostic: implementations may write to stdout, a log file, an
    append-only DB table, or a SIEM. Handlers depend only on this contract.
    """

    @abstractmethod
    async def record(self, event: Any) -> None: ...
