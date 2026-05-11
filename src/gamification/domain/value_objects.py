
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class LevelInfo:
    level: int
    rank_tier: str       
    rank_name: str
    current_xp: int
    xp_for_next_level: int | None   
    xp_progress: int               
    xp_needed: int | None           

@dataclass(frozen=True)
class WorkoutRewards:
    total_xp: int

    def __add__(self, other: "WorkoutRewards") -> "WorkoutRewards":
        return WorkoutRewards(
            total_xp=self.total_xp + other.total_xp,
        )