from __future__ import annotations
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from src.user.domain.models import FitnessGoal, Gender

if TYPE_CHECKING:
    from src.user.application.commands import UpdateFitnessCommand, UpdateUserInfoCommand


class UserInfoUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50)
    avatar_url: str | None = Field(None, max_length=500)

    def to_command(self, user_id: int) -> UpdateUserInfoCommand:
        from src.user.application.commands import UpdateUserInfoCommand
        return UpdateUserInfoCommand(user_id=user_id, name=self.name, avatar_url=self.avatar_url)


class FitnessProfileUpdate(BaseModel):
    weight: float | None = Field(None, gt=0, lt=700, description="kg")
    height: float | None = Field(None, gt=0, lt=300, description="cm")
    age: int | None = Field(None, gt=0, lt=150)
    gender: Gender | None = None
    fitness_goal: FitnessGoal | None = None

    def to_command(self, user_id: int) -> UpdateFitnessCommand:
        from src.user.application.commands import UpdateFitnessCommand
        return UpdateFitnessCommand(
            user_id=user_id,
            weight=self.weight,
            height=self.height,
            age=self.age,
            gender=self.gender,
            fitness_goal=self.fitness_goal,
        )


class FitnessProfileResponse(BaseModel):
    weight: float | None
    height: float | None
    age: int | None
    gender: Gender | None
    fitness_goal: FitnessGoal | None
    bmi: float | None = None

    model_config = ConfigDict(from_attributes=True)


class FullProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: str | None
    is_verified: bool
    is_2fa_enabled: bool
    oauth_provider: str | None
    fitness: FitnessProfileResponse | None

    model_config = ConfigDict(from_attributes=True)