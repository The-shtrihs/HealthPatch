from datetime import datetime

from pydantic import BaseModel, Field


class LeaveCommentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    comment_id: int
    plan_id: int
    user_id: int
    text: str
    created_at: datetime


class LikePlanResponse(BaseModel):
    liked: bool


class UnlikePlanResponse(BaseModel):
    unliked: bool


class SavePlanResponse(BaseModel):
    saved: bool


class UnsavePlanResponse(BaseModel):
    unsaved: bool


class RedactCommentResponse(BaseModel):
    redacted_comment_id: int


class PlanCommentsResponse(BaseModel):
    plan_id: int
    page: int
    page_size: int
    total: int
    comments: list[CommentResponse]
