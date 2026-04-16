from src.user.domain.models import (FitnessGoal, FitnessProfileDomain, Gender, UserProfileDomain)
from src.models.user import User, UserProfile

def _orm_to_fitness(p: UserProfile | None) -> FitnessProfileDomain | None:
    if not p:
        return None
    return FitnessProfileDomain(
        weight=p.weight, height=p.height, age=p.age,
        gender=Gender(p.gender) if p.gender else None,
        fitness_goal=FitnessGoal(p.fitness_goal) if p.fitness_goal else None,
    )


def _orm_to_profile(u: User) -> UserProfileDomain:
    return UserProfileDomain(
        id=u.id, name=u.name, email=u.email,
        avatar_url=u.avatar_url, is_verified=u.is_verified,
        is_active=u.is_active, is_2fa_enabled=u.is_2fa_enabled,
        oauth_provider=u.oauth_provider,
        fitness=_orm_to_fitness(getattr(u, "profile", None)),
    )