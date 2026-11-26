"""Conversation and message endpoint tests."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from typing import AsyncGenerator

from app.models import Provider, Model, User, Conversation, Message, Agent
from app.core.security import create_access_token, create_refresh_token


@pytest_asyncio.fixture(autouse=True)
async def test_engine_fixture():
    """Use the existing test engine from conftest."""
    pass


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session using existing engine."""
    from app.core.database import engine
    async with AsyncSession(engine, expire_on_commit=False) as session:
        # Create all tables
        from app.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield session


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_provider(test_db: AsyncSession, test_user: User) -> Provider:
    """Create a test provider."""
    provider = Provider(
        owner_id=test_user.id,
        name="Test OpenAI",
        provider_type="openai-compatible",
        base_url="https://api.openai.com/v1",
        api_key_encrypted="hashed",
        config={},
    )
    test_db.add(provider)
    await test_db.commit()
    await test_db.refresh(provider)
    return provider


@pytest_asyncio.fixture
async def test_model(test_provider: Provider, test_db: AsyncSession) -> Model:
    """Create a test model under the test provider."""
    model = Model(
        provider_id=test_provider.id,
        model_id="test-model-id",
        display_name="Test Model",
        model_type="chat",
        context_window=128000,
        supports_streaming=True,
        supports_tools=True,
    )
    test_db.add(model)
    await test_db.commit()
    await test_db.refresh(model)
    return model


@pytest_asyncio.fixture
async def test_agent(test_user: User, test_model: Model) -> Agent:
    """Create a test agent with the test model."""
    agent = Agent(
        owner_id=test_user.id,
        model_id=test_model.id,
        name="Test Agent",
        description="A test agent",
        system_prompt="You are a test assistant.",
        temperature=0.7,
        max_tokens=1000,
        tools=[],
        config={},
    )
    test_db.add(agent)
    await test_db.commit()
    await test_db.refresh(agent)
    return agent


@pytest.fixture
async def test_conversation(test_db: AsyncSession, test_agent: Agent) -> Conversation:
    """Create a test conversation linked to the test agent."""
    conversation = Conversation(
        owner_id=test_agent.owner_id,
        title="Test Conversation",
        agent_id=test_agent.id,
        is_active=True,
    )
    test_db.add(conversation)
    await test_db.commit()
    await test_db.refresh(conversation)
    return conversation


@pytest_asyncio.fixture
async def auth_cookies(test_user: User) -> dict:
    """Create auth cookies for test user."""
    access_token = create_access_token(subject=str(test_user.id), roles=test_user.roles)
    refresh_token = create_refresh_token(subject=str(test_user.id))
    return {"access_token": access_token, "refresh_token": refresh_token}


@pytest.mark.asyncio
async def test_create_message_basic(async_client: AsyncClient, auth_cookies: dict, test_conversation: Conversation):
    """Test creating a basic message without model_id."""
    response = await async_client.post(
        f"/conversations/{test_conversation.id}/messages",
        json={"role": "user", "content": "Hello, world!"},
        cookies=auth_cookies,
    )
    assert response.status_code == 201, f"Failed to create message: {response.status_code} {response.text}"
    data = response.json()
    assert data["role"] == "user"
    assert data["content"] == "Hello, world!"
    # model_id should be None when not provided
    assert data["model_id"] is None


@pytest.mark.asyncio
async def test_create_message_with_model_id(async_client: AsyncClient, auth_cookies: dict, test_conversation: Conversation, test_model: Model):
    """Test creating a message with model_id."""
    response = await async_client.post(
        f"/conversations/{test_conversation.id}/messages",
        json={"role": "user", "content": "Hello with model", "model_id": test_model.id},
        cookies=auth_cookies,
    )
    assert response.status_code == 201, f"Failed to create message: {response.status_code} {response.text}"
    data = response.json()
    assert data["role"] == "user"
    assert data["content"] == "Hello with model"
    assert data["model_id"] == test_model.id


@pytest.mark.asyncio
async def test_create_message_invalid_model_id(async_client: AsyncClient, auth_cookies: dict, test_conversation: Conversation):
    """Test creating a message with invalid model_id (not owned by user)."""
    response = await async_client.post(
        f"/conversations/{test_conversation.id}/messages",
        json={"role": "user", "content": "Hello with invalid model", "model_id": 999999},
        cookies=auth_cookies,
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower() or "model" in data["detail"].lower()


@pytest.mark.asyncio
async def test_list_messages(async_client: AsyncClient, auth_cookies: dict, test_conversation: Conversation, test_model: Model):
    """Test listing messages in a conversation."""
    # Create messages with and without model_id
    await async_client.post(
        f"/conversations/{test_conversation.id}/messages",
        json={"role": "user", "content": "Message 1", "model_id": test_model.id},
        cookies=auth_cookies,
    )
    await async_client.post(
        f"/conversations/{test_conversation.id}/messages",
        json={"role": "assistant", "content": "Message 2"},
        cookies=auth_cookies,
    )

    # List messages
    response = await async_client.get(
        f"/conversations/{test_conversation.id}/messages",
        cookies=auth_cookies,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Check that model_id is stored correctly
    assert data[0]["model_id"] == test_model.id
    assert data[1]["model_id"] is None
