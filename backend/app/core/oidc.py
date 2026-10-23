"""OIDC authentication utilities for Keycloak integration."""

import httpx
from typing import Optional
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.security import generate_state, generate_code_verifier, generate_code_challenge


settings = get_settings()


class TokenResponse(BaseModel):
    """OIDC token response."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None


class UserInfo(BaseModel):
    """OIDC user info response."""
    sub: str
    preferred_username: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    realm_access: Optional[dict] = None


class OIDCClient:
    """Keycloak OIDC client for authorization code flow with PKCE."""

    def __init__(self):
        self.issuer_url = settings.oidc_issuer_url.rstrip("/")
        self.client_id = settings.oidc_client_id
        self.client_secret = settings.oidc_client_secret
        self.redirect_uri = settings.oidc_redirect_uri
        self.scopes = settings.oidc_scopes
        self._discovery_cache: Optional[dict] = None

    async def _get_discovery(self) -> dict:
        """Fetch and cache OIDC discovery document."""
        if self._discovery_cache is None:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.issuer_url}/.well-known/openid-configuration"
                )
                response.raise_for_status()
                self._discovery_cache = response.json()
        return self._discovery_cache

    def get_authorization_url(self) -> tuple[str, str, str]:
        """
        Generate authorization URL with PKCE.
        Returns: (authorization_url, state, code_verifier)
        """
        state = generate_state()
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scopes,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        query = "&".join(f"{k}={httpx._utils.quote(v)}" for k, v in params.items())
        auth_url = f"{self.issuer_url}/protocol/openid-connect/auth?{query}"

        return auth_url, state, code_verifier

    async def exchange_code(
        self,
        code: str,
        code_verifier: str,
    ) -> TokenResponse:
        """Exchange authorization code for tokens."""
        discovery = await self._get_discovery()
        token_endpoint = discovery["token_endpoint"]

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": code_verifier,
        }

        if self.client_secret:
            data["client_secret"] = self.client_secret

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return TokenResponse(**response.json())

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        discovery = await self._get_discovery()
        token_endpoint = discovery["token_endpoint"]

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
        }

        if self.client_secret:
            data["client_secret"] = self.client_secret

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return TokenResponse(**response.json())

    async def get_user_info(self, access_token: str) -> UserInfo:
        """Fetch user info from Keycloak."""
        discovery = await self._get_discovery()
        userinfo_endpoint = discovery["userinfo_endpoint"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return UserInfo(**response.json())

    async def logout_url(self, id_token_hint: Optional[str] = None) -> str:
        """Generate logout URL."""
        discovery = await self._get_discovery()
        logout_endpoint = discovery.get("end_session_endpoint", f"{self.issuer_url}/protocol/openid-connect/logout")

        params = {
            "client_id": self.client_id,
            "post_logout_redirect_uri": settings.oidc_logout_uri,
        }
        if id_token_hint:
            params["id_token_hint"] = id_token_hint

        query = "&".join(f"{k}={httpx._utils.quote(v)}" for k, v in params.items())
        return f"{logout_endpoint}?{query}"


# Global OIDC client instance
oidc_client = OIDCClient()