"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "beacon-hub"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./beacon_hub.db"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Security
    secret_key: str = Field(default="dev-secret-change-in-production-please-use-longer-key", min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OIDC / Keycloak
    oidc_enabled: bool = True
    oidc_issuer_url: str = "http://localhost:8080/realms/beacon-hub"
    oidc_client_id: str = "beacon-hub"
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = "http://localhost:3000/callback"
    oidc_scopes: str = "openid profile email roles"
    oidc_logout_uri: str = "http://localhost:3000"

    # LLM
    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None
    llm_timeout_seconds: int = 60

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()