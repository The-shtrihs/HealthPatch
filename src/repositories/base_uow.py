from sqlalchemy.ext.asyncio import AsyncSession

class BaseUnitOfWork:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._owns_transaction = False
        self._nested_transaction = None

    async def __aenter__(self):
        # Tests and some integration flows may provide a session that already has
        # an open transaction. In that case we use a savepoint instead of opening
        # a second root transaction.
        self._owns_transaction = not self._session.in_transaction()
        if self._owns_transaction:
            await self._session.begin()
        else:
            self._nested_transaction = await self._session.begin_nested()
        return self

    async def __aexit__(self, exc_type, _exc_val, _exc_tb):
        if self._owns_transaction:
            if exc_type is not None:
                await self._session.rollback()
            else:
                await self._session.commit()
            return

        if self._nested_transaction is None:
            return

        if exc_type is not None:
            await self._nested_transaction.rollback()
        else:
            await self._nested_transaction.commit()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
