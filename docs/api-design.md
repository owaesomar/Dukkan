# API design

Use `/api/v1` for versioned application endpoints. Private merchant endpoints authenticate the browser session, resolve active store membership, and validate action permissions. State-changing authenticated routes require the CSRF header. Public storefront endpoints will be separate and use explicit allowlisted response schemas.

Implemented endpoints:

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`
- `POST /api/v1/stores`, `GET /api/v1/stores`, `GET /api/v1/stores/{store_id}`, `PATCH /api/v1/stores/{store_id}`
- `GET/POST /api/v1/stores/{store_id}/members`, `PATCH/DELETE /api/v1/stores/{store_id}/members/{user_id}`
- `GET/POST /api/v1/stores/{store_id}/categories`, `PATCH /api/v1/stores/{store_id}/categories/{category_id}`
- `GET/POST /api/v1/stores/{store_id}/products`, `GET/PATCH /api/v1/stores/{store_id}/products/{product_id}`
- `POST/PATCH /api/v1/stores/{store_id}/products/{product_id}/variants[/{variant_id}]`
- `POST /api/v1/stores/{store_id}/products/{product_id}/media`; `GET .../media/{media_id}/url` returns a short-lived private object URL.
- `GET /api/v1/stores/{store_id}/inventory`, `POST /api/v1/stores/{store_id}/inventory/variants/{variant_id}/adjustments`
- `GET /api/v1/public/stores/{store_slug}`, `GET .../categories`, `GET .../products?q=&category_id=`, and `GET .../products/{product_id}` expose only active stores and published products.
- `POST /api/v1/public/stores/{store_slug}/checkout` accepts COD checkout with an `Idempotency-Key`; `GET .../orders/{order_code}` requires `X-Order-Tracking-Token`.
- `GET /api/v1/stores/{store_id}/orders`, `GET .../orders/{order_id}`, and `PATCH .../orders/{order_id}/status` are membership-authorized merchant order endpoints.
- `GET /api/v1/stores/{store_id}/analytics/overview` returns date-bounded, store-scoped order, paid revenue by currency, customer, product, and stock metrics.
- `GET /api/v1/stores/{store_id}/subscription`, `PUT .../subscription`, and `POST .../subscription/cancel` let owners/admins read and change the store plan/status. `GET /api/v1/subscription-plans` lists available plans.
- `/api/v1/platform-admin/*` provides global overview, merchant/store/subscription lists, store and merchant lifecycle controls, plan management, admin grants, and audit events. Every route requires an explicit platform-admin grant.

Request/response data uses Pydantic schemas, never raw ORM serialization. Missing store membership returns a non-disclosing 404; an authenticated member without a required permission receives 403. Prices use integer minor units and a three-letter currency code. Inventory changes are append-only adjustment records and are serialized by row locks. Checkout validates current catalog and stock inside a transaction, reserves stock, and replays matching idempotency keys safely.

The first platform administrator is granted operationally after account creation with the bootstrap command in [deployment.md](deployment.md); normal accounts cannot self-assign global access. Subscription plan management is described in [subscriptions.md](subscriptions.md). The current subscription API records plan selection and cancellation without collecting payments.
