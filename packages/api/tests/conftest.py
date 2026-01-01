"""Pytest fixtures for travelers.ai API tests."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from travelers_api.core.config import Settings, get_settings
from travelers_api.core.database import Base, get_db
from travelers_api.main import app

# Test database URL (use in-memory SQLite for speed, or a test Postgres DB)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def get_test_settings() -> Settings:
    """Get settings configured for testing."""
    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",  # type: ignore
        secret_key="test-secret-key-that-is-at-least-32-chars-long",
        llm_provider="none",
        redis_url="redis://localhost:6379/1",
        allowed_origins=["http://localhost:3000"],
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for a test."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = get_test_settings

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user registration data."""
    return {
        "email": f"test-{uuid4().hex[:8]}@example.com",
        "password": "testpassword123",
        "display_name": "Test User",
        "preferred_language": "en",
    }


@pytest.fixture
async def authenticated_client(
    client: AsyncClient, sample_user_data: dict[str, Any]
) -> AsyncGenerator[tuple[AsyncClient, dict[str, Any]], None]:
    """Create a test client with an authenticated user."""
    # Register a new user
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    assert response.status_code == 201
    data = response.json()

    # Add auth header to client
    access_token = data["tokens"]["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    yield client, data["user"]

    # Clean up
    client.headers.pop("Authorization", None)


@pytest.fixture
def sample_city_data() -> dict[str, Any]:
    """Sample city data for testing."""
    return {
        "name": "Test City",
        "country": "Test Country",
        "wikidata_id": "Q12345",
        "coordinates": {"lat": 40.7128, "lng": -74.0060},
    }


@pytest.fixture
def sample_poi_data() -> dict[str, Any]:
    """Sample POI data for testing."""
    return {
        "name": "Test POI",
        "poi_type": "monument",
        "summary": "A test point of interest",
        "wikidata_id": "Q54321",
        "coordinates": {"lat": 40.7128, "lng": -74.0060},
        "estimated_visit_duration": 60,
    }
