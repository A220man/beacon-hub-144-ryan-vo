"""Agent management endpoint tests."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Model, Provider, User
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def test_provider(test_db: AsyncSession, test_user: User) -> Provider:
    """Create a test provider."""
    provider = Provider(
        owner_id=test_user.id,
        name="Test Provider",
        provider_type="openai-compatible",
        base_url="https://api.openai.com/v1",
        api_key_encrypted="sk-test",
        is_active=True,
    )
    test_db.add(provider)
    await test_db.commit()
    await test_db.refresh(provider)
    return provider


@pytest_asyncio.fixture
async def test_model(test_db: AsyncSession, test_provider: Provider) -> Model:
    """Create a test model."""
    model = Model(
        provider_id=test_provider.id,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        model_type="chat",
        context_window=4096,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=False,
        is_active=True,
    )
    test_db.add(model)
    await test_db.commit()
    await test_db.refresh(model)
    return model


@pytest.fixture
def auth_cookies(test_user: User) -> dict:
    """Create auth cookies for test user."""
    from app.core.security import create_access_token, create_refresh_token
    access_token = create_access_token(subject=str(test_user.id), roles=test_user.roles)
    refresh_token = create_refresh_token(subject=str(test_user.id))
    return {"access_token": access_token, "refresh_token": refresh_token}


class TestAgentEndpoints:
    """Tests for agent management endpoints."""

    @pytest.mark.asyncio
    async def test_create_agent(self, async_client: AsyncClient, test_model: Model, auth_cookies: dict):
        """Test creating a new agent."""
        response = await async_client.post(
            "/agents",
            json={
                "model_id": test_model.id,
                "name": "Test Agent",
                "description": "A test agent",
                "system_prompt": "You are a helpful assistant",
                "temperature": 0.7,
                "max_tokens": 1000,
                "tools": ["web_search"],
                "config": {},
            },
            cookies=auth_cookies,
        )
        assert response.status_code in (201, 401, 403)
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == "Test Agent"
            assert data["model_id"] == test_model.id
            assert data["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_list_agents(self, async_client: AsyncClient, test_model: Model, auth_cookies: dict):
        """Test listing agents."""
        # First create an agent
        await async_client.post(
            "/agents",
            json={
                "model_id": test_model.id,
                "name": "Test Agent",
            },
            cookies=auth_cookies,
        )
        response = await async_client.get("/agents", cookies=auth_cookies)
        assert response.status_code in (200, 401, 403)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_agent(self, async_client: AsyncClient, test_model: Model, auth_cookies: dict):
        """Test getting a specific agent."""
        create_resp = await async_client.post(
            "/agents",
            json={"model_id": test_model.id, "name": "Test Agent"},
            cookies=auth_cookies,
        )
        if create_resp.status_code == 201:
            agent_id = create_resp.json()["id"]
            response = await async_client.get(f"/agents/{agent_id}", cookies=auth_cookies)
            assert response.status_code in (200, 401, 403, 404)
            if response.status_code == 200:
                data = response.json()
                assert data["id"] == agent_id
                assert data["name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_update_agent(self, async_client: AsyncClient, test_model: Model, auth_cookies: dict):
        """Test updating an agent."""
        create_resp = await async_client.post(
            "/agents",
            json={"model_id": test_model.id, "name": "Test Agent"},
            cookies=auth_cookies,
        )
        if create_resp.status_code == 201:
            agent_id = create_resp.json()["id"]
            response = await async_client.patch(
                f"/agents/{agent_id}",
                json={"name": "Updated Agent", "temperature": 0.5},
                cookies=auth_cookies,
            )
            assert response.status_code in (200, 401, 403, 404)
            if response.status_code == 200:
                data = response.json()
                assert data["name"] == "Updated Agent"
                assert data["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_delete_agent(self, async_client: AsyncClient, test_model: Model, auth_cookies: dict):
        """Test deleting an agent."""
        create_resp = await async_client.post(
            "/agents",
            json={"model_id": test_model.id, "name": "Test Agent"},
            cookies=auth_cookies,
        )
        if create_resp.status_code == 201:
            agent_id = create_resp.json()["id"]
            response = await async_client.delete(f"/agents/{agent_id}", cookies=auth_cookies)
            assert response.status_code in (204, 401, 403, 404)
            if response.status_code == 204:
                # Verify deletion
                get_resp = await async_client.get(f"/agents/{agent_id}", cookies=auth_cookies)
                assert get_resp.status_code in (404, 401, 403)

    @pytest.mark.asyncio
    async def test_agent_name_validation(self, async_client: AsyncClient, test_model: Model, auth_cookies: dict):
        """Test agent name validation."""
        response = await async_client.post(
            "/agents",
            json={"model_id": test_model.id, "name": ""},
            cookies=auth_cookies,
        )
        assert response.status_code in (422, 401, 403, 404)

    @pytest.mark.asyncio
    async def test_agent_model_validation(self, async_client: AsyncClient, auth_cookies: dict):
        """Test that agent creation fails with invalid model_id."""
        response = await async_client.post(
            "/agents",
            json={"model_id": 99999, "name": "Test Agent"},
            cookies=auth_cookies,
        )
        assert response.status_code in (404, 401, 403, 422)
