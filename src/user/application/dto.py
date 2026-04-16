from dataclasses import dataclass
from src.user.domain.models import FitnessGoal, Gender


@dataclass
class UpdateUserInfoCommand:
    name: str | None
    avatar_url: str | None


@dataclass
class UpdateFitnessCommand:
    weight: float | None
    height: float | None
    age: int | None
    gender: Gender | None
    fitness_goal: FitnessGoal | None