from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.activity import ActivityRepository


class ActivityUnitOfWork:
    def __init__(self, session: AsyncSession):
        self._session = session
        self.activity = ActivityRepository(session)

    async def __aenter__(self):
        await self._session.begin()
        return self

    async def __aexit__(self, exc_type, _exc_val, _exc_tb):
        if exc_type is not None:
            await self._session.rollback()
        else:
            await self._session.commit()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
