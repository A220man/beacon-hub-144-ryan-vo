"""Pytest configuration and fixtures for backend tests."""

import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-chars-long"
os.environ["OIDC_ENABLED"] = "false"

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import create_app
from app.models import User


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def app(test_db):
    """Create test FastAPI app with overridden dependencies."""
    app = create_app()

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture(scope="function")
def client(app) -> TestClient:
    """Create synchronous test client."""
    return TestClient(app)


@pytest_asyncio.fixture(scope="function")
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        oidc_sub="test-sub-123",
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        roles=["user"],
        is_admin=False,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """Create auth headers with JWT token for test user."""
    token = create_access_token(subject=str(test_user.id), roles=test_user.roles)
    return {"Authorization": f"Bearer {token}", "Cookie": f"access_token={token}"}


@pytest.fixture(scope="function")
def auth_cookies(test_user: User) -> dict:
    """Create auth cookies with JWT token for test user."""
    from app.core.security import create_access_token, create_refresh_token
    access_token = create_access_token(subject=str(test_user.id), roles=test_user.roles)
    refresh_token = create_refresh_token(subject=str(test_user.id))
    return {"access_token": access_token, "refresh_token": refresh_token}


@pytest.fixture(scope="function")
def mock_oidc_client():
    """Mock OIDC client for testing."""
    mock = AsyncMock()
    mock.get_authorization_url.return_value = (
        "https://keycloak.example.com/auth?client_id=test",
        "test-state",
        "test-verifier",
    )
    mock.exchange_code.return_value = MagicMock(
        access_token="test-access-token",
        token_type="bearer",
        expires_in=3600,
        refresh_token="test-refresh-token",
        id_token="test-id-token",
    )
    mock.get_user_info.return_value = MagicMock(
        sub="test-sub-123",
        preferred_username="testuser",
        email="test@example.com",
        name="Test User",
        realm_access={"roles": ["user"]},
    )
    return mock