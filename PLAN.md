# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

project-skeleton

## Roadmap

### project-skeleton — Project skeleton with FastAPI backend and React frontend

Status: done

Acceptance:
- Backend FastAPI app runs with health endpoint
- Frontend React+Vite+TypeScript app builds
- Docker Compose with backend, frontend, Keycloak, PostgreSQL
- Basic OIDC authentication flow configured
- SQLite for development, PostgreSQL for production

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/security.py`, `backend/app/core/oidc.py`, `backend/app/api/health.py`, `backend/app/api/auth.py`, `backend/app/api/providers.py`, `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`, `backend/requirements.txt`, `backend/tests/conftest.py`, `backend/tests/test_health.py`, `backend/tests/test_auth.py`, `backend/tests/test_providers.py`, `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/components/Layout.tsx`, `frontend/src/components/Health.tsx`, `frontend/src/components/Providers.tsx`, `frontend/src/components/Health.test.tsx`, `frontend/src/hooks/useAuth.tsx`, `frontend/src/api/client.ts`, `frontend/src/types/api.ts`, `frontend/src/index.css`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/src/test-setup.ts`, `frontend/index.html`, `frontend/nginx.conf`, `docker-compose.yaml`, `compose.yaml`, `backend/Dockerfile`, `frontend/Dockerfile`, `portfolio.json`, `README.md`, `LICENSE`, `CHANGELOG.md`, `pyproject.toml`, `.gitignore`, `.env.example`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_health.py`, `backend/tests/test_auth.py`, `backend/tests/test_providers.py`, `frontend/src/components/Health.test.tsx`

### provider-model-management — Multiple models per OpenAI-compatible provider connection

Status: planned

Acceptance:
- Configure provider credentials once
- Register multiple model IDs under same connection
- Bots can select model from connection
- Tasks/routines can override bot's default model

### agent-chat-workflow — Agent chat with model selection and sandbox execution

Status: planned

Acceptance:
- Create agents with selected model
- Chat interface with streaming responses
- Sandbox execution for code/tools
- Conversation persistence

### onboarding-flow — Guided onboarding with stepper and integration cards

Status: planned

Acceptance:
- Root redirects to sign-in
- Onboarding stepper with progress
- Integration provider cards with logos
- Desktop-aware server settings window

### image-video-generation — Image and video generation model support

Status: planned

Acceptance:
- Configure image/video generation providers
- Bots/tasks can use generation models
- Display generated media in chat/results
- Progress status for long-running video generation

