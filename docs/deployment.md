# Deployment plan

Local infrastructure is defined in the root Docker Compose file. Production should run the frontend on a static hosting platform and the backend as a container with managed PostgreSQL and Redis. S3-compatible media storage is optional: when configured, set `S3_BUCKET`, `S3_REGION`, optional `S3_ENDPOINT_URL`, and the host's AWS-compatible credentials through its secret/configuration system. Without a bucket, product image uploads are unavailable, but existing frontend assets and the rest of the app continue to work. Production startup rejects non-HTTPS or wildcard CORS origins and local database/Redis hosts. Restrict CORS to production frontend origins, terminate TLS at the host/load balancer, and keep database backups with tested restore procedures.

The production API image is `backend/Dockerfile`. It runs as a non-root user, exposes a readiness health check at `/health/ready`, and uses configurable worker and port values. CI builds the image after backend, frontend, and Python dependency checks pass. Pushing a `v*` tag publishes `ghcr.io/<owner>/<repository>/api:<tag>`. Configure a protected GitHub `production` environment with required reviewers if desired and the `BACKEND_DEPLOY_HOOK_URL` and `FRONTEND_DEPLOY_HOOK_URL` secrets to enable the deployment hook workflow. The hook URLs must target services that deploy the intended immutable release; the current generic hooks do not pin an image digest or coordinate frontend/backend versions.

For each release: run CI; review migration SQL; take and verify a backup when schema changes require it; apply Alembic migrations as a separate release step; deploy the immutable backend image and frontend build; verify `/health/live`, `/health/ready`, login, storefront browsing, and checkout. The container entrypoint does not run migrations. Prefer forward-only corrective migrations for data/schema changes; never run destructive migrations automatically. Roll back the application image and frontend artifact independently only when they remain compatible with the current schema. If a migration is not backward compatible, use the reviewed recovery plan and restore the database backup before routing traffic to a compatible image.

## PostgreSQL backup and restore

Run `scripts/backup-postgres.sh` from a secured operator environment with `DATABASE_URL` set and a protected `BACKUP_DIRECTORY`. The script writes a custom-format archive with restrictive file permissions and verifies its archive table of contents. Encrypt and copy backups to storage in a separate failure domain, define retention, and alert on missed backups; this repository script does not provide offsite storage or scheduling.

Restore only into a new or intentionally cleared recovery database, after confirming the target name and backup timestamp. Use a PostgreSQL client version compatible with the server major version:

```sh
pg_restore --no-owner --no-acl --exit-on-error \
  --dbname="$RECOVERY_DATABASE_URL" /secure/backups/dukkan-YYYYMMDDTHHMMSSZ.dump
cd backend
DATABASE_URL="$RECOVERY_DATABASE_URL" uv run alembic check
```

After restoring, verify the Alembic revision, representative row counts, application readiness, and key merchant/storefront flows before switching traffic. The Phase 7 local rehearsal restored an empty PostgreSQL 15 test database, downgraded one revision, upgraded to head `0004_saas_management`, and passed `alembic check`. This is a procedure rehearsal, not a production recovery-time or recovery-point guarantee.

## Rollback and monitoring

The API provides `/health/live` for process liveness and `/health/ready` for database and Redis readiness. Requests carry an `X-Request-ID`; the same ID appears in structured JSON logs. The current application logs errors but does not export metrics, traces, or alerts to a hosted monitoring service. Configure external uptime checks and log retention/alerting before production use. No production environment, deployment credentials, monitoring provider, or rollback target is configured in this repository, so actual deployment and provider rollback have not been exercised.

After applying migrations and creating the first trusted operator account, grant initial global access from a controlled backend environment with `uv run python -m app.modules.platform_admin.bootstrap operator@example.com`. The command only grants access to an existing account. Subsequent grants and revocations are available to platform admins and are audited. Never expose bootstrap access through a public endpoint.

Subscription plans and store plan status are tracked in PostgreSQL. No payment processor, invoicing, or automatic recurring charge is configured yet; displayed recurring revenue is an estimate based on active plan assignments.
