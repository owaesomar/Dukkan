# Testing strategy

Use fast unit tests for pure rules; PostgreSQL-backed integration tests for repositories, constraints, and transactions; security tests for cross-tenant denial; and frontend component/E2E tests for merchant and storefront flows. SQLite is not a substitute for PostgreSQL tenant constraints or RLS behavior.

The backend tests cover session authentication, role restrictions, tenant-scoped categories/products, cross-store composite foreign key rejection, image type validation and metadata upload (storage mocked), inventory audit records, negative stock rejection, concurrent stock decreases, simultaneous duplicate-checkout idempotency, request IDs, readiness responses, and production configuration validation. Set `TEST_DATABASE_URL` to a dedicated database whose name ends in `_test`:

```sh
cd backend
TEST_DATABASE_URL=postgresql+psycopg://dukkan:dukkan@localhost:5432/dukkan_test uv run pytest
```

The fixture drops and recreates application tables in that database and refuses names without the `_test` suffix. CI applies migrations and checks schema drift against an ephemeral PostgreSQL service before running tests. Product media tests mock S3; configure a real S3-compatible bucket to validate object storage credentials and lifecycle outside unit tests. `scripts/storefront-load-smoke.py` runs bounded, read-only storefront requests against a deployed URL and reports latency percentiles; run it against a staging deployment to establish a capacity baseline. A local container performance baseline has not been recorded. Frontend storefront and Playwright end-to-end tests remain future work.

The backup script's archive validation and restore path were rehearsed against an isolated PostgreSQL 15 test database. The restored schema was rolled back by one Alembic revision, migrated forward to `0004_saas_management`, and passed `alembic check`. Docker image build and deployment hooks still need to be exercised in CI and a configured staging/production environment.
