from dataclasses import dataclass

from src.user.domain.models import FitnessGoal, Gender


@dataclass(frozen=True)
class FitnessReadModel:
    weight: float | None
    height: float | None
    age: int | None
    gender: Gender | None
    fitness_goal: FitnessGoal | None
    bmi: float | None


@dataclass(frozen=True)
class FullProfileReadModel:
    id: int
    name: str
    email: str
    avatar_url: str | None
    is_verified: bool
    is_2fa_enabled: bool
    oauth_provider: str | None
    fitness: FitnessReadModel | None
