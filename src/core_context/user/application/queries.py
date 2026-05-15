from dataclasses import dataclass


@dataclass(frozen=True)
class GetMyProfileQuery:
    user_id: int
