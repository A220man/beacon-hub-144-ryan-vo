# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-23

### Added
- Project skeleton with FastAPI backend and React+Vite+TypeScript frontend
- Health check endpoints (`/health`, `/health/ready`, `/health/live`)
- OIDC authentication flow with Keycloak (authorization code + PKCE)
- Provider management API (CRUD for LLM provider connections)
- Model management API (CRUD for models under providers, multiple models per provider)
- SQLite for development, PostgreSQL for production
- Docker Compose with backend, frontend, Keycloak, PostgreSQL
- Frontend components: Layout, Health dashboard, Providers & Models management
- JWT-based authentication with HttpOnly cookies and CSRF protection
- Audit logging for security-relevant events
- Comprehensive test suite (16 backend tests passing)

### Infrastructure
- Multi-stage Dockerfiles for backend (Python 3.12) and frontend (Node 24 + nginx)
- NGINX reverse proxy with API routing and SPA fallback
- Health checks for all services
- Non-root users in containers
- Resource limits for all services

### Security
- PBKDF2-HMAC-SHA256 password hashing
- JWT tokens with configurable expiration
- PKCE for OIDC authorization code flow
- State and nonce validation
- HttpOnly, SameSite=Lax, Secure cookies
- Input validation on all API endpoints

### Documentation
- README with architecture diagram, API reference, configuration guide
- MIT License
- Portfolio.json manifest
- .env.example template