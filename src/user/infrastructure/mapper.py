from src.models.user import User, UserProfile
from src.user.domain.models import FitnessGoal, FitnessProfileDomain, Gender, UserProfileDomain
from src.user.application.read_models import FitnessReadModel, FullProfileReadModel


def _orm_to_fitness(p: UserProfile | None) -> FitnessProfileDomain | None:
    if not p:
        return None
    return FitnessProfileDomain(
        weight=p.weight,
        height=p.height,
        age=p.age,
        gender=Gender(p.gender) if p.gender else None,
        fitness_goal=FitnessGoal(p.fitness_goal) if p.fitness_goal else None,
    )


def _orm_to_profile(u: User) -> UserProfileDomain:
    return UserProfileDomain(
        id=u.id,
        name=u.name,
        email=u.email,
        avatar_url=u.avatar_url,
        is_verified=u.is_verified,
        is_active=u.is_active,
        is_2fa_enabled=u.is_2fa_enabled,
        oauth_provider=u.oauth_provider,
        fitness=_orm_to_fitness(getattr(u, "profile", None)),
    )

def _orm_to_fitness_rm(profile: UserProfile | None) -> FitnessReadModel | None:
    if not profile:
        return None
    weight = profile.weight
    height = profile.height
    bmi: float | None = None
    if weight and height and height > 0:
        bmi = round(weight / (height / 100) ** 2, 1)
    return FitnessReadModel(
        weight=weight,
        height=height,
        age=profile.age,
        gender=Gender(profile.gender) if profile.gender else None,
        fitness_goal=FitnessGoal(profile.fitness_goal) if profile.fitness_goal else None,
        bmi=bmi,
    )
def _orm_to_full_profile_rm(user: User) -> FullProfileReadModel:
    fitness_orm = getattr(user, "profile", None)
    return FullProfileReadModel(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        is_verified=user.is_verified,
        is_2fa_enabled=user.is_2fa_enabled,
        oauth_provider=user.oauth_provider,
        fitness=_orm_to_fitness_rm(fitness_orm),
    )