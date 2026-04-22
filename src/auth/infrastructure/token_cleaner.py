from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from src.auth.domain.interfaces import ITokenCleaner
from src.models.user import RefreshToken 

class SqlAlchemyTokenCleaner(ITokenCleaner):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def clear_expired_tokens(self) -> int:
        stmt = (
            delete(RefreshToken)
            .where(RefreshToken.expires_at < datetime.now(timezone.utc))
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount