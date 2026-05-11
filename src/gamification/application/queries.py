from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class GetGamificationProfileQuery:
    user_id: int
