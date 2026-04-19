from dataclasses import dataclass
from enum import StrEnum


class FitnessGoal(StrEnum):
    WEIGHT_LOSS = "weight loss"
    MUSCLE_GAIN = "muscle gain"
    STRENGTH_BUILDING = "strength building"
    ENDURANCE = "endurance"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class FitnessProfileDomain:
    weight: float | None
    height: float | None
    age: int | None
    gender: Gender | None
    fitness_goal: FitnessGoal | None

    def calc_bmi(self) -> float | None:
        if self.weight and self.height and self.height > 0:
            return round(self.weight / (self.height / 100) ** 2, 1)
        return None


@dataclass
class UserProfileDomain:
    id: int
    name: str
    email: str
    avatar_url: str | None
    is_verified: bool
    is_active: bool
    is_2fa_enabled: bool
    oauth_provider: str | None
    fitness: FitnessProfileDomain | None

    def update_info(self, name: str | None = None, avatar_url: str | None = None) -> None:
        if name is not None:
            self.name = name
        if avatar_url is not None:
            self.avatar_url = avatar_url

    def update_fitness(
        self,
        weight: float | None = None,
        height: float | None = None,
        age: int | None = None,
        gender: Gender | None = None,
        fitness_goal: FitnessGoal | None = None,
    ) -> None:
        if self.fitness is None:
            self.fitness = FitnessProfileDomain(
                weight=weight, height=height, age=age,
                gender=gender, fitness_goal=fitness_goal,
            )
        else:
            if weight is not None:
                self.fitness.weight = weight
            if height is not None:
                self.fitness.height = height
            if age is not None:
                self.fitness.age = age
            if gender is not None:
                self.fitness.gender = gender
            if fitness_goal is not None:
                self.fitness.fitness_goal = fitness_goal

    def deactivate(self) -> None:
        self.is_active = False