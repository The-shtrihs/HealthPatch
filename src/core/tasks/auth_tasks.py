from src.auth.infrastructure.token_cleaner import SqlAlchemyTokenCleaner
from src.core.database import get_session


async def clear_expired_tokens():
    print("Starting expired token cleanup...")
    async with get_session() as session:
        cleaner = SqlAlchemyTokenCleaner(session)
        deleted_count = await cleaner.clear_expired_tokens()
    print(f"Expired token cleanup completed successfully! Deleted {deleted_count} tokens.")
