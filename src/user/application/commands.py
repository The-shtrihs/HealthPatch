from dataclasses import dataclass
from src.user.domain.models import FitnessGoal, Gender


@dataclass(frozen=True)
class UpdateUserInfoCommand:
    user_id: int
    name: str | None
    avatar_url: str | None


@dataclass(frozen=True)
class UpdateFitnessCommand:
    user_id: int
    weight: float | None
    height: float | None
    age: int | None
    gender: Gender | None
    fitness_goal: FitnessGoal | None


@dataclass(frozen=True)
class DeleteAccountCommand:
    user_id: int