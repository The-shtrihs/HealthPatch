from fastapi import APIRouter, Depends, status

from src.core_context.auth.contracts.dependencies import CurrentUser as UserDomain
from src.core_context.auth.contracts.dependencies import get_current_user
from src.core_context.user.application.commands import DeleteAccountCommand
from src.core_context.user.application.handlers.delete_account import DeleteAccountCommandHandler
from src.core_context.user.application.handlers.get_profile import GetMyProfileQueryHandler
from src.core_context.user.application.handlers.update_fitness import UpdateFitnessCommandHandler
from src.core_context.user.application.handlers.update_user_info import UpdateUserInfoCommandHandler
from src.core_context.user.application.queries import GetMyProfileQuery
from src.core_context.user.presentation.dependencies import (
    get_delete_account_handler,
    get_get_profile_handler,
    get_update_fitness_handler,
    get_update_user_info_handler,
)
from src.core_context.user.presentation.schemas import FitnessProfileResponse, FitnessProfileUpdate, FullProfileResponse, UserInfoUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me", response_model=FullProfileResponse)
async def get_my_profile(
    current_user: UserDomain = Depends(get_current_user),
    handler: GetMyProfileQueryHandler = Depends(get_get_profile_handler),
):
    result = await handler.handle(GetMyProfileQuery(user_id=current_user.id))
    return FullProfileResponse.model_validate(result)


@router.patch("/me", response_model=FullProfileResponse)
async def update_my_info(
    data: UserInfoUpdate,
    current_user: UserDomain = Depends(get_current_user),
    cmd_handler: UpdateUserInfoCommandHandler = Depends(get_update_user_info_handler),
    query_handler: GetMyProfileQueryHandler = Depends(get_get_profile_handler),
):
    await cmd_handler.handle(data.to_command(user_id=current_user.id))
    result = await query_handler.handle(GetMyProfileQuery(user_id=current_user.id))
    return FullProfileResponse.model_validate(result)


@router.put("/me/fitness", response_model=FitnessProfileResponse)
async def update_fitness_profile(
    data: FitnessProfileUpdate,
    current_user: UserDomain = Depends(get_current_user),
    cmd_handler: UpdateFitnessCommandHandler = Depends(get_update_fitness_handler),
    query_handler: GetMyProfileQueryHandler = Depends(get_get_profile_handler),
):
    await cmd_handler.handle(data.to_command(user_id=current_user.id))
    result = await query_handler.handle(GetMyProfileQuery(user_id=current_user.id))
    return FitnessProfileResponse.model_validate(result.fitness)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    current_user: UserDomain = Depends(get_current_user),
    handler: DeleteAccountCommandHandler = Depends(get_delete_account_handler),
):
    await handler.handle(DeleteAccountCommand(user_id=current_user.id))
