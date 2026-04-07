from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient, patch
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.base import Base
from src.core.config import get_settings
from src.core.database import get_session
from src.core.main import app
from src.core.redis import get_redis
from src.routes.dependencies import get_mail_service

settings = get_settings()

engine = create_async_engine(settings.database_url, poolclass=NullPool)


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


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, fake_redis, mock_mail_service):
    async def override_get_session():
        yield db_session

    async def override_get_redis():
        return fake_redis

    async def override_get_mail_service():  
        return mock_mail_service

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis] = override_get_redis
    app.dependency_overrides[get_mail_service] = override_get_mail_service  

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

    from src.models.user import User

    await db_session.execute(update(User).where(User.email == registered_user["email"]).values(is_verified=True))
    await db_session.commit()

    resp = await client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


