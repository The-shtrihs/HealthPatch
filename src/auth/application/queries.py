from dataclasses import dataclass

from src.auth.domain.models import UserDomain


@dataclass(frozen=True)
class GetMeQuery:
    user: UserDomain 