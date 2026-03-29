from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BadRequestError, NotFoundError
from src.repositories.social import SocialRepository


class SocialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SocialRepository(db)

    async def like_plan(self, user_id: int, plan_id: int) -> dict[str, bool]:
        async with self.db.begin():
            await self._ensure_plan_exists(plan_id)
            created = await self.repo.add_like(plan_id=plan_id, user_id=user_id)
            return {"liked": created}

    async def unlike_plan(self, user_id: int, plan_id: int) -> dict[str, bool]:
        async with self.db.begin():
            await self._ensure_plan_exists(plan_id)
            removed = await self.repo.remove_like(plan_id=plan_id, user_id=user_id)
            return {"unliked": removed}

    async def save_plan(self, user_id: int, plan_id: int) -> dict[str, bool]:
        async with self.db.begin():
            await self._ensure_plan_exists(plan_id)
            created = await self.repo.add_bookmark(plan_id=plan_id, user_id=user_id)
            return {"saved": created}

    async def unsave_plan(self, user_id: int, plan_id: int) -> dict[str, bool]:
        async with self.db.begin():
            await self._ensure_plan_exists(plan_id)
            removed = await self.repo.remove_bookmark(plan_id=plan_id, user_id=user_id)
            return {"unsaved": removed}

    async def leave_comment(self, user_id: int, plan_id: int, text: str) -> dict:
        cleaned_text = text.strip()
        if not cleaned_text:
            raise BadRequestError(message="Comment text cannot be empty")

        async with self.db.begin():
            await self._ensure_plan_exists(plan_id)
            comment = await self.repo.create_comment(plan_id=plan_id, user_id=user_id, text=cleaned_text)
            return {
                "comment_id": comment.id,
                "plan_id": comment.plan_id,
                "user_id": comment.user_id,
                "text": comment.text,
                "created_at": comment.created_at,
            }

    async def get_plan_comments(self, plan_id: int, page: int, page_size: int) -> dict:
        if page < 1:
            raise BadRequestError(message="Page must be greater than or equal to 1")
        if page_size < 1:
            raise BadRequestError(message="Page size must be greater than or equal to 1")

        await self._ensure_plan_exists(plan_id)
        comments, total = await self.repo.get_plan_comments_paginated(
            plan_id=plan_id,
            page=page,
            page_size=page_size,
        )

        return {
            "plan_id": plan_id,
            "page": page,
            "page_size": page_size,
            "total": total,
            "comments": [
                {
                    "comment_id": comment.id,
                    "plan_id": comment.plan_id,
                    "user_id": comment.user_id,
                    "text": comment.text,
                    "created_at": comment.created_at,
                }
                for comment in comments
            ],
        }

    async def redact_comment(self, user_id: int, comment_id: int) -> dict[str, int]:
        async with self.db.begin():
            comment = await self.repo.get_comment_for_user(comment_id=comment_id, user_id=user_id)
            if comment is None:
                raise NotFoundError(resource="Comment", resource_id=comment_id)

            await self.repo.delete_comment(comment)
            return {"redacted_comment_id": comment_id}

    async def _ensure_plan_exists(self, plan_id: int) -> None:
        exists = await self.repo.plan_exists(plan_id)
        if not exists:
            raise NotFoundError(resource="Workout plan", resource_id=plan_id)
