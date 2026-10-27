# ADR 0002: Opaque browser sessions and store memberships

- Status: Accepted
- Date: 2026-10-27

## Context

Merchant accounts can belong to multiple stores, so authentication and store authorization must remain separate. Browser requests need revocable credentials and cross-site request forgery protection.

## Decision

Use random opaque session secrets in HttpOnly cookies, store only SHA-256 digests in PostgreSQL, expire and revoke sessions server-side, and require a matching CSRF cookie/header whose digest is stored with the session for mutations. A store membership grants access to that store only. Role checks and active membership predicates are performed in a shared authorization dependency and again when role changes are serialized under a store row lock.

## Consequences

Logout and administrative revocation take effect immediately. Each private request performs a session lookup. Cookie deployment requires HTTPS in production and exact CORS origins. Email verification, password reset, MFA, and login audit history remain future work.
