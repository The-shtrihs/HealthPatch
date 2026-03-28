from fastapi import APIRouter, Depends, status

from src.models.user import User
from src.routes.dependencies import get_current_user, get_profile_service
from src.schemas.profile import FitnessProfileResponse, FitnessProfileUpdate, FullProfileResponse, UserInfoUpdate
from src.services.profile import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me", response_model=FullProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    return await profile_service.get_full_profile(current_user.id)


@router.patch("/me", response_model=FullProfileResponse)
async def update_my_info(
    data: UserInfoUpdate,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    return await profile_service.update_user_info(current_user, data)


@router.put("/me/fitness", response_model=FitnessProfileResponse)
async def update_fitness_profile(
    data: FitnessProfileUpdate,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    return await profile_service.update_fitness_profile(current_user.id, data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    await profile_service.delete_account(current_user)
    