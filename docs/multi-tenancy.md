# Multi-tenancy and authorization boundaries

A store is the tenant. `users` and `auth_sessions` are platform identity tables. Each merchant store is a tenant root; `store_memberships` has the composite primary key `(store_id, user_id)` and a constrained role. Store slugs are globally unique for path routing.

Private routes require an authenticated user and an active membership for the requested store. Store queries include membership/store scope; tenant-owned tables carry `store_id`, use scoped repository methods, and add composite foreign keys for tenant-owned parent associations. Public storefront access uses separate public schemas/services. Platform administrator grants use a separate permission namespace and are audited.

The PostgreSQL migrations add users, server-side sessions, stores, memberships, categories, products, variants, media metadata, inventory, customers, orders, subscriptions, and platform audit events. APIs scope tenant queries by the authorized store, and composite foreign keys reject cross-store associations. PostgreSQL tests verify cross-merchant denial, direct composite-constraint rejection, concurrent inventory updates, and duplicate-checkout idempotency. PostgreSQL RLS remains a planned defense-in-depth measure, not yet enabled.
