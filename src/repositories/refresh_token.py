from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, token_value: str, user_id: int, expires_at: datetime, device_info: str | None) -> RefreshToken:
        db_token = RefreshToken(token=token_value, user_id=user_id, expires_at=expires_at, device_info=device_info)
        self.db.add(db_token)
        await self.db.commit()
        await self.db.refresh(db_token)
        return db_token

    async def get_active_token(self, token: str) -> RefreshToken | None:
        result = await self.db.scalars(select(RefreshToken).where(RefreshToken.token == token, RefreshToken.is_revoked.is_(False)))
        return result.first()

    async def mark_as_revoked(self, db_token: RefreshToken) -> None:
        db_token.is_revoked = True
        await self.db.commit()

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self.db.execute(update(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False)).values(is_revoked=True))
        await self.db.commit()
