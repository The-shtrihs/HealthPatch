from typing import Annotated

from fastapi import APIRouter, Depends

from src.core_context.auth.contracts.dependencies import CurrentUser, get_current_user
from src.core_context.gamification.application.handlers.get_profile import GetGamificationProfileQuery
from src.core_context.gamification.domain.leveling import calculate_level
from src.core_context.gamification.presentation.dependencies import ProfileQueryHandlerDep
from src.core_context.gamification.presentation.schemas import (
    GamificationProfileResponse,
    LevelInfoSchema,
)

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get(
    "/me",
    response_model=GamificationProfileResponse,
    summary="Мій gamification профіль",
)
async def get_my_gamification_profile(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    query_handler: ProfileQueryHandlerDep,
) -> GamificationProfileResponse:
    profile = await query_handler.handle(GetGamificationProfileQuery(user_id=current_user.id))

    total_xp = profile.total_xp if profile is not None else 0

    level_info = calculate_level(total_xp)

    return GamificationProfileResponse(
        user_id=current_user.id,
        total_xp=total_xp,
        level_info=LevelInfoSchema.from_domain(level_info),
    )
