from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.base import Base
from src.core.config import get_settings
from src.core.database import get_session
from src.core.dependencies import get_event_bus
from src.core.main import app
from src.core.redis import get_redis
from src.core_context.activity.application.event_handlers import register_activity_event_handlers
from src.core_context.auth.application.event_handlers import register_auth_event_handlers
from src.core_context.auth.presentation.dependencies import get_mail_service
from src.core_context.gamification.application.event_handlers import register_gamification_handlers
from src.core_context.nutrition.application.event_handlers import register_nutrition_event_handlers
from src.shared.infrastructure.daily_claim_store import DailyClaimStore
from src.shared.infrastructure.event_bus import EventBus

settings = get_settings()

engine = create_async_engine(settings.database_url, poolclass=NullPool)
session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        yield session
        await session.close()
        await transaction.rollback()


@pytest_asyncio.fixture
async def fake_redis():
    r = fakeredis.aioredis.FakeRedis()
    yield r
    await r.flushall()
    await r.aclose()


@pytest_asyncio.fixture
async def mock_mail_service():
    service = MagicMock()
    service.send_verification_email = AsyncMock()
    service.send_password_reset_email = AsyncMock()
    return service


class FakeDailyClaimStore(DailyClaimStore):
    async def try_claim(self, user_id: int, target_date) -> bool:
        return True


class FakeMealEntryQueries:
    async def count_for_day(self, user_id: int, day) -> int:
        return 0


@pytest_asyncio.fixture
async def fake_event_bus():
    bus = EventBus()
    register_gamification_handlers(bus, session_factory, FakeMealEntryQueries(), FakeDailyClaimStore())
    register_nutrition_event_handlers(bus)
    register_auth_event_handlers(bus)
    register_activity_event_handlers(bus)
    bus.arq_pool = AsyncMock()
    return bus


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, fake_redis, mock_mail_service, fake_event_bus):
    async def override_get_session():
        yield db_session

    async def override_get_redis():
        return fake_redis

    async def override_get_mail_service():
        return mock_mail_service

    async def override_get_event_bus():
        return fake_event_bus

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis] = override_get_redis
    app.dependency_overrides[get_mail_service] = override_get_mail_service
    app.dependency_overrides[get_event_bus] = override_get_event_bus
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "Test1234!",
        "password_confirm": "Test1234!",
    }
    await client.post("/auth/register", json=payload)
    return payload


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user, db_session) -> dict:
    from sqlalchemy import update

    from src.core_context.user.infrastructure.orm import User

    await db_session.execute(update(User).where(User.email == registered_user["email"]).values(is_verified=True))
    await db_session.commit()

    resp = await client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
