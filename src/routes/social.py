from fastapi import APIRouter, Depends, Query

from src.models.user import User
from src.routes.dependencies import get_current_user, get_social_service
from src.schemas.social import (
    CommentResponse,
    LeaveCommentRequest,
    LikePlanResponse,
    PlanCommentsResponse,
    RedactCommentResponse,
    SavePlanResponse,
    UnlikePlanResponse,
    UnsavePlanResponse,
)
from src.services.social import SocialService

router = APIRouter(prefix="/social", tags=["Social"])


@router.post("/plans/{plan_id}/like", response_model=LikePlanResponse, status_code=201)
async def like_plan(
    plan_id: int,
    social_service: SocialService = Depends(get_social_service),
    current_user: User = Depends(get_current_user),
):
    return await social_service.like_plan(user_id=current_user.id, plan_id=plan_id)


@router.delete("/plans/{plan_id}/like", response_model=UnlikePlanResponse)
async def unlike_plan(
    plan_id: int,
    social_service: SocialService = Depends(get_social_service),
    current_user: User = Depends(get_current_user),
):
    return await social_service.unlike_plan(user_id=current_user.id, plan_id=plan_id)


@router.post("/plans/{plan_id}/save", response_model=SavePlanResponse, status_code=201)
async def save_plan(
    plan_id: int,
    social_service: SocialService = Depends(get_social_service),
    current_user: User = Depends(get_current_user),
):
    return await social_service.save_plan(user_id=current_user.id, plan_id=plan_id)


@router.delete("/plans/{plan_id}/save", response_model=UnsavePlanResponse)
async def unsave_plan(
    plan_id: int,
    social_service: SocialService = Depends(get_social_service),
    current_user: User = Depends(get_current_user),
):
    return await social_service.unsave_plan(user_id=current_user.id, plan_id=plan_id)


@router.post("/plans/{plan_id}/comments", response_model=CommentResponse, status_code=201)
async def leave_comment(
    plan_id: int,
    payload: LeaveCommentRequest,
    social_service: SocialService = Depends(get_social_service),
    current_user: User = Depends(get_current_user),
):
    return await social_service.leave_comment(user_id=current_user.id, plan_id=plan_id, text=payload.text)


@router.get("/plans/{plan_id}/comments", response_model=PlanCommentsResponse)
async def get_plan_comments(
    plan_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    social_service: SocialService = Depends(get_social_service),
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    return await social_service.get_plan_comments(plan_id=plan_id, page=page, page_size=page_size)


@router.delete("/comments/{comment_id}", response_model=RedactCommentResponse)
async def redact_comment(
    comment_id: int,
    social_service: SocialService = Depends(get_social_service),
    current_user: User = Depends(get_current_user),
):
    return await social_service.redact_comment(user_id=current_user.id, comment_id=comment_id)
