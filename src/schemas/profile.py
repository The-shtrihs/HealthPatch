from pydantic import BaseModel, ConfigDict, Field

from src.models.user import FitnessGoal, Gender


class FitnessProfileUpdate(BaseModel):
    weight: float | None = Field(None, gt=0, lt=700, description="Weight in kg")
    height: float | None = Field(None, gt=0, lt=300, description="Height in cm")
    age: int | None = Field(None, gt=0, lt=150)
    gender: Gender | None = None
    fitness_goal: FitnessGoal | None = None


class UserInfoUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50)
    avatar_url: str | None = Field(None, max_length=500)


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
    profile: FitnessProfileResponse | None

    model_config = ConfigDict(from_attributes=True)
