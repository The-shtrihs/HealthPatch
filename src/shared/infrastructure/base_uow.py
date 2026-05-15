from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.contracts.integration_event import IntegrationEvent


class BaseUnitOfWork:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._owns_transaction = False
        self._nested_transaction = None
        self.events: list[Any] = []
        self.integration_events: list[IntegrationEvent] = []

    async def __aenter__(self):
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
                self.events.clear()
                self.integration_events.clear()
            else:
                await self._session.commit()
            return

        if self._nested_transaction is None:
            return

        if exc_type is not None:
            await self._nested_transaction.rollback()
            self.events.clear()
            self.integration_events.clear()
        else:
            await self._nested_transaction.commit()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()

    def add_integration_event(self, event: IntegrationEvent) -> None:
        self.integration_events.append(event)
