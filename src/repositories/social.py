from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.activity import WorkoutPlan
from src.models.social import Bookmark, Comment, Like


class SocialRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def plan_exists(self, plan_id: int) -> bool:
        stmt = select(WorkoutPlan.id).where(WorkoutPlan.id == plan_id)
        return (await self.db.execute(stmt)).scalar_one_or_none() is not None

    async def add_like(self, plan_id: int, user_id: int) -> bool:
        stmt = (
            insert(Like)
            .values(plan_id=plan_id, user_id=user_id)
            .on_conflict_do_nothing(index_elements=["plan_id", "user_id"])
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def remove_like(self, plan_id: int, user_id: int) -> bool:
        stmt = select(Like).where(and_(Like.plan_id == plan_id, Like.user_id == user_id))
        like = (await self.db.scalars(stmt)).first()

        if like is None:
            return False

        await self.db.delete(like)
        await self.db.flush()
        return True

    async def add_bookmark(self, plan_id: int, user_id: int) -> bool:
        stmt = (
            insert(Bookmark)
            .values(plan_id=plan_id, user_id=user_id)
            .on_conflict_do_nothing(index_elements=["plan_id", "user_id"])
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def remove_bookmark(self, plan_id: int, user_id: int) -> bool:
        stmt = select(Bookmark).where(and_(Bookmark.plan_id == plan_id, Bookmark.user_id == user_id))
        bookmark = (await self.db.scalars(stmt)).first()

        if bookmark is None:
            return False

        await self.db.delete(bookmark)
        await self.db.flush()
        return True

    async def create_comment(self, plan_id: int, user_id: int, text: str) -> Comment:
        comment = Comment(plan_id=plan_id, user_id=user_id, text=text)
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def get_plan_comments_paginated(
        self,
        plan_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[Comment], int]:
        offset = (page - 1) * page_size

        comments_stmt = (
            select(Comment)
            .where(Comment.plan_id == plan_id)
            .order_by(Comment.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        comments = (await self.db.scalars(comments_stmt)).all()

        total_stmt = select(func.count()).select_from(Comment).where(Comment.plan_id == plan_id)
        total = (await self.db.execute(total_stmt)).scalar_one()

        return list(comments), int(total)

    async def get_comment_for_user(self, comment_id: int, user_id: int) -> Comment | None:
        stmt = select(Comment).where(and_(Comment.id == comment_id, Comment.user_id == user_id))
        result = await self.db.scalars(stmt)
        return result.first()

    async def delete_comment(self, comment: Comment) -> None:
        await self.db.delete(comment)
        await self.db.flush()
