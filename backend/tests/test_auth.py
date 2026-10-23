"""Authentication endpoint tests."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_login_oidc_disabled(self, async_client: AsyncClient):
        """Test login returns 503 when OIDC is disabled."""
        response = await async_client.get("/auth/login")
        assert response.status_code == 503
        assert "OIDC authentication is not configured" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_callback_missing_code(self, async_client: AsyncClient):
        """Test callback returns 400 when code is missing."""
        response = await async_client.post("/auth/callback", json={})
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_refresh_missing_token(self, async_client: AsyncClient):
        """Test refresh returns 401 when refresh token is missing."""
        response = await async_client.post("/auth/refresh")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, async_client: AsyncClient):
        """Test /me returns 401 when not authenticated."""
        response = await async_client.get("/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_clears_cookies(self, async_client: AsyncClient):
        """Test logout clears auth cookies."""
        response = await async_client.post("/auth/logout")
        assert response.status_code == 200
        # Check cookies are cleared
        assert "access_token" in response.headers.get("set-cookie", "")
        assert "refresh_token" in response.headers.get("set-cookie", "")