from typing import Annotated

from fastapi import APIRouter, Depends

from src.auth.presentation.dependencies import get_current_user
from src.gamification.application.handlers.get_profile import GetGamificationProfileQuery
from src.gamification.domain.leveling import calculate_level
from src.gamification.presentation.dependencies import ProfileQueryHandlerDep
from src.gamification.presentation.schemas import (
    GamificationProfileResponse,
    LevelInfoSchema,
)
from src.models.user import User

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get(
    "/me",
    response_model=GamificationProfileResponse,
    summary="Мій gamification профіль",
)
async def get_my_gamification_profile(
    current_user: Annotated[User, Depends(get_current_user)],
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
