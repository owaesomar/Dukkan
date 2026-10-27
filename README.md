# Dukkan

Dukkan is a multi-tenant commerce platform for independent merchants. The repository is a modular monolith: a React/TypeScript frontend and FastAPI API backed by PostgreSQL, with Redis for authentication rate limits and future cache/job support.

## Requirements

- Python 3.12+
- Node.js 20+
- Docker Desktop (or another running Docker Engine) with Docker Compose
- `uv` for backend dependency management

## Local development

1. Start Docker Desktop, then create the local backend settings file: `cp backend/.env.example backend/.env`.
2. Start PostgreSQL and Redis from the repository root: `docker compose up -d postgres redis`.
3. Install backend dependencies and migrate the database: `cd backend && uv sync --locked --all-groups && uv run alembic upgrade head`.
4. Start the API in that terminal: `uv run uvicorn app.main:app --reload`.
5. In another terminal, install the locked frontend dependencies and start Vite: `cd frontend && npm ci && npm run dev`.

To preview populated storefronts locally, run `cd backend && uv run python -m scripts.seed_demo_stores`. This development-only command is safe to repeat and creates six sample shops with four published products each. It prints the demo merchant emails and shared local password. Sample shop and product photography is bundled in `frontend/public/demo-images`.

The Vite development server proxies `/api` and `/health` to the API. Open `http://localhost:5173`; check API liveness at `http://localhost:8000/health/live` and readiness at `http://localhost:8000/health/ready`. The local S3 bucket setting can remain blank for flows that do not upload images. Run `docker compose down` to stop the services; add `-v` only when you intend to delete the local database and Redis data.

## Authentication and tenancy

Registration and login create opaque, revocable server-side sessions using HttpOnly cookies. Browser write requests send the CSRF cookie value in `X-CSRF-Token`. Accounts can own multiple stores; access to each store requires an active membership. See [docs/authentication.md](docs/authentication.md), [docs/authorization.md](docs/authorization.md), and [docs/multi-tenancy.md](docs/multi-tenancy.md).

## Validation

- Backend: `cd backend && uv run pytest` (set `TEST_DATABASE_URL` to a dedicated database ending in `_test` for integration tests)
- Backend lint/types: `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app`
- Frontend: `cd frontend && npm run lint && npm test && npm run build`

## Implementation status

Phases 2–6 implement identity, tenant authorization, catalog/inventory, storefront/cart, COD checkout/order fulfillment, merchant analytics/team/subscription dashboards, and separately authorized platform administration. Phase 7 local hardening and backup/restore rehearsal are documented; production deployment, monitoring, external security audit, and recovery objectives still need provider configuration and validation. Subscription records and plan prices are managed in-app; payment collection is not integrated. PostgreSQL RLS remains future work. Bootstrap initial platform access for an existing account with `cd backend && uv run python -m app.modules.platform_admin.bootstrap admin@example.com`. Product image upload requires S3-compatible bucket configuration. See [docs/implementation-plan.md](docs/implementation-plan.md), [docs/deployment.md](docs/deployment.md), [docs/authorization.md](docs/authorization.md), and [docs/subscriptions.md](docs/subscriptions.md).
