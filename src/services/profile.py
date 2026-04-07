from src.core.exceptions import NotFoundError
from src.models.user import User, UserProfile
from src.repositories.profile import ProfileRepository
from src.schemas.profile import FitnessProfileResponse, FitnessProfileUpdate, FullProfileResponse, UserInfoUpdate


def _calc_bmi(weight: float | None, height: float | None) -> float | None:
    if weight and height and height > 0:
        return round(weight / (height / 100) ** 2, 1)
    return None


def _build_fitness_response(profile: UserProfile | None) -> FitnessProfileResponse | None:
    if not profile:
        return None
    return FitnessProfileResponse(
        weight=profile.weight,
        height=profile.height,
        age=profile.age,
        gender=profile.gender,
        fitness_goal=profile.fitness_goal,
        bmi=_calc_bmi(profile.weight, profile.height),
    )


class ProfileService:
    def __init__(self, profile_repo: ProfileRepository):
        self.profile_repo = profile_repo

    async def get_full_profile(self, user_id: int) -> FullProfileResponse:
        user = await self.profile_repo.get_full_user(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return FullProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            is_2fa_enabled=user.is_2fa_enabled,
            oauth_provider=user.oauth_provider,
            profile=_build_fitness_response(user.profile),
        )

    async def update_user_info(self, current_user: User, data: UserInfoUpdate) -> FullProfileResponse:
        if data.model_dump(exclude_none=True):
            user = await self.profile_repo.update_user_info(
                user=current_user,
                data=data,
            )
            return await self.get_full_profile(user.id)
        return await self.get_full_profile(current_user.id)

    async def update_fitness_profile(self, user_id: int, data: FitnessProfileUpdate) -> FitnessProfileResponse:
        profile = await self.profile_repo.update_fitness_profile(user_id=user_id, data=data)
        return _build_fitness_response(profile)

    async def delete_account(self, user: User) -> None:
        await self.profile_repo.deactivate_user(user)
