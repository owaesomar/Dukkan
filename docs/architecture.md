# Architecture overview

## Initial repository audit

The adjacent starter repository (`../Dukkan`) is a small FastAPI/SQLAlchemy experiment. It has a `Store` table with `id`, `name`, and globally unique `slug`, plus a basic service/router split. It had no users, authentication, memberships, tenant-owned resources, migrations, frontend, or tests. Its app ran `Base.metadata.create_all()` at startup, enabled SQL echo, and exposed unauthenticated store operations. The update route was malformed, the get route passed arguments in the wrong order and returned `201`, and store listing was not scoped. The adjacent starter and its untracked files were left untouched.

The `dukkan production` workspace was empty at task start. It now contains the application foundations through Phase 7 local hardening and recovery rehearsal. External hosting, monitoring, and deployment remain unconfigured.

## Target architecture

Use a modular monolith with a React/TypeScript SPA and a FastAPI API. PostgreSQL is the source of truth. Redis supports rate limits, cache entries, and background work. S3-compatible object storage holds media. Keep modules organized by business capability, with HTTP, use-case, and persistence responsibilities distinct where complexity warrants it.

```text
frontend/                 React + TypeScript app
backend/app/
  core/                   settings, logging, security primitives, middleware
  db/                     SQLAlchemy base and session lifecycle
  common/                 pagination and shared response contracts
  modules/
    auth/ users/ stores/ memberships/
    catalog/ inventory/ customers/ orders/
    subscriptions/ analytics/ platform_admin/
  integrations/           storage, payments, email
backend/alembic/          reviewed schema migrations
backend/tests/            unit, integration, and security tests
docs/                     architecture, contracts, operations, decisions
```

## Request boundaries

Private merchant routes authenticate an opaque server-side session and require an active membership for the requested store. A permission dependency checks membership role/action, and queries include the authorized `store_id`. Membership mutations lock the store row and re-check the actor's active role. Platform operations use a separate explicit platform-admin grant and audit log. Public storefront routes resolve active stores and expose only published catalog fields; they do not call merchant authorization paths.

## Current implementation

Phases 2–6 implement registration/login, store/membership authorization, catalog and inventory, public storefront/cart, COD checkout and order fulfillment, merchant analytics/team/subscription dashboards, and a separately authorized platform administration dashboard. Phase 7 adds validated production configuration, request correlation, readiness probes, CI audits, and backup/restore procedures. PostgreSQL and Redis run through Docker Compose; Alembic manages identity, tenancy, catalog, inventory, order, subscription, and platform audit schemas. Payment collection, RLS, hosted monitoring, external deployment and rollback, and production backup scheduling remain unconfigured. Product images use private S3-compatible object storage and require bucket configuration. Production readiness is not claimed.
