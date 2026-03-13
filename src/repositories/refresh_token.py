from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import RefreshToken


class RefreshTokenRepository:
    @staticmethod
    async def create(db: AsyncSession, token_value: str, user_id: int, expires_at: datetime, device_info: str | None) -> RefreshToken:
        db_token = RefreshToken(token=token_value, user_id=user_id, expires_at=expires_at, device_info=device_info)
        db.add(db_token)
        await db.commit()
        await db.refresh(db_token)
        return db_token

    @staticmethod
    async def get_active_token(db: AsyncSession, token: str) -> RefreshToken | None:
        result = await db.scalars(select(RefreshToken).where(RefreshToken.token == token, RefreshToken.is_revoked.is_(False)))
        return result.first()

    @staticmethod
    async def mark_as_revoked(db: AsyncSession, db_token: RefreshToken) -> None:
        db_token.is_revoked = True
        await db.commit()

    @staticmethod
    async def revoke_all_for_user(db: AsyncSession, user_id: int) -> None:
<<<<<<< HEAD
        await db.execute(
            update(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False)).values(is_revoked=True)
        )
        await db.commit()
=======
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False)))
        await db.commit()
>>>>>>> 6c55c7eb15e959b292ee782b7bb1fef4632d72e2
