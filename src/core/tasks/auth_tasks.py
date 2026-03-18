from src.core.database import get_session
from src.repositories.refresh_token import RefreshTokenRepository


async def clear_expired_tokens():
    print("Starting expired token cleanup...")
    async with get_session() as session:
        await RefreshTokenRepository.delete_expired_tokens(session)
        await session.commit()
    print("Expired token cleanup completed successfully!")