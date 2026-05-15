from dataclasses import dataclass

from src.core_context.auth.domain.models import UserDomain


@dataclass(frozen=True)
class GetMeQuery:
    user: UserDomain
