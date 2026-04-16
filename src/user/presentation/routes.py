from fastapi import APIRouter, Depends, status

from src.auth.domain.models import UserDomain
from src.auth.presentation.dependencies import get_current_user  
from src.user.application.dto import UpdateFitnessCommand, UpdateUserInfoCommand
from src.user.application.use_cases import UserProfileUseCases
from src.user.presentation.dependencies import get_user_profile_use_cases
from src.user.presentation.schemas import (
    FitnessProfileResponse, FitnessProfileUpdate,
    FullProfileResponse, UserInfoUpdate,
)

router = APIRouter(prefix="/profile", tags=["Profile"])


def _fitness_response(fitness) -> FitnessProfileResponse | None:
    if not fitness:
        return None
    return FitnessProfileResponse(
        weight=fitness.weight, height=fitness.height, age=fitness.age,
        gender=fitness.gender, fitness_goal=fitness.fitness_goal,
        bmi=fitness.calc_bmi(),  
    )


def _profile_response(p) -> FullProfileResponse:
    return FullProfileResponse(
        id=p.id, name=p.name, email=p.email, avatar_url=p.avatar_url,
        is_verified=p.is_verified, is_2fa_enabled=p.is_2fa_enabled,
        oauth_provider=p.oauth_provider, profile=_fitness_response(p.fitness),
    )


@router.get("/me", response_model=FullProfileResponse)
async def get_my_profile(
    current_user: UserDomain = Depends(get_current_user),
    user_profile_use_cases: UserProfileUseCases = Depends(get_user_profile_use_cases),
):
    return _profile_response(await user_profile_use_cases.get_profile(current_user.id))


@router.patch("/me", response_model=FullProfileResponse)
async def update_my_info(
    data: UserInfoUpdate,
    current_user: UserDomain = Depends(get_current_user),
    user_profile_use_cases: UserProfileUseCases = Depends(get_user_profile_use_cases),
):
    return _profile_response(
        await user_profile_use_cases.update_info(current_user.id, UpdateUserInfoCommand(name=data.name, avatar_url=data.avatar_url))
    )


@router.put("/me/fitness", response_model=FitnessProfileResponse)
async def update_fitness_profile(
    data: FitnessProfileUpdate,
    current_user: UserDomain = Depends(get_current_user),
    user_profile_use_cases: UserProfileUseCases = Depends(get_user_profile_use_cases),
):
    fitness = await user_profile_use_cases.update_fitness(
        current_user.id,
        UpdateFitnessCommand(
            weight=data.weight, height=data.height, age=data.age,
            gender=data.gender, fitness_goal=data.fitness_goal,
        ),
    )
    return _fitness_response(fitness)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    current_user: UserDomain = Depends(get_current_user),
    user_profile_use_cases: UserProfileUseCases = Depends(get_user_profile_use_cases),
):
    await user_profile_use_cases.delete_account(current_user.id)