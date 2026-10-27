# Phased implementation checklist

- [x] Phase 1 foundation: monorepo skeleton, FastAPI settings/logging/health, React/Vite shell, PostgreSQL and Redis Compose services, Alembic environment, CI baseline, architecture and initial ERD documentation.
- [x] Phase 1 completion: generated frontend lockfile and production backend image.
- [ ] Phase 1 remaining: add Playwright coverage and validate Compose workflows against local services.
- [x] Phase 2 identity and tenancy: users, secure auth/session lifecycle, stores, memberships, role/action authorization, tenant-scoped persistence, reviewed migration, PostgreSQL cross-tenant tests.
- [x] Phase 3 catalog: categories, products, variants, media, inventory and tenant-safe constraints.
- [x] Phase 4 storefront: active-store routing, published catalog search/filtering, product detail, responsive pages, and persistent store-scoped cart.
- [x] Phase 5 checkout: validated customer/shipping details, locked inventory reservations, COD orders, idempotency, secure order tracking, and merchant fulfillment transitions.
- [x] Phase 6 SaaS management: merchant dashboard, staff roles and controls, tenant-scoped sales analytics, explicit platform-admin grants and audit log, store lifecycle controls, and subscription plans/status.
- [x] Phase 7 local hardening: production settings validation, request correlation and sanitized errors, database/Redis readiness, non-root API image, locked dependency install, CI security audits, and concurrency coverage for duplicate checkout.
- [x] Phase 7 recovery tooling: secure custom-format PostgreSQL backup script; isolated PostgreSQL 15 restore rehearsal; one-revision downgrade/upgrade; final Alembic schema check at `0004_saas_management`.
- [x] Phase 7 operations documentation and bounded read-only storefront load-smoke utility.
- [ ] Phase 7 external validation: run Node advisory audit with network access; build and run the container; establish staging performance/monitoring baselines; configure and exercise deployment hooks and provider rollback; validate offsite backup schedule/retention and production recovery objectives.
