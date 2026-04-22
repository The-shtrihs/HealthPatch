from src.user.application.queries import GetMyProfileQuery
from src.user.application.read_models import FitnessReadModel, FullProfileReadModel
from src.user.domain.errors import UserNotFoundError
from src.user.domain.interfaces import IUserProfileRepository
from src.user.domain.models import FitnessProfileDomain


class GetMyProfileQueryHandler:
    def __init__(self, repo: IUserProfileRepository):
        self._repo = repo

    async def handle(self, query: GetMyProfileQuery) -> FullProfileReadModel:
        profile = await self._repo.get_full_profile(query.user_id)
        if not profile:
            raise UserNotFoundError(query.user_id)
        return FullProfileReadModel(
            id=profile.id,
            name=profile.name,
            email=profile.email,
            avatar_url=profile.avatar_url,
            is_verified=profile.is_verified,
            is_2fa_enabled=profile.is_2fa_enabled,
            oauth_provider=profile.oauth_provider,
            fitness=_to_fitness_read_model(profile.fitness),
        )


def _to_fitness_read_model(fitness: FitnessProfileDomain | None) -> FitnessReadModel | None:
    if not fitness:
        return None
    return FitnessReadModel(
        weight=fitness.weight,
        height=fitness.height,
        age=fitness.age,
        gender=fitness.gender,
        fitness_goal=fitness.fitness_goal,
        bmi=fitness.calc_bmi(),
    )
