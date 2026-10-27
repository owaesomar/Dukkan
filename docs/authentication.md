# Authentication

Phase 2 adds email/password accounts and server-side sessions. Passwords are hashed with Argon2id through `pwdlib`; random session and CSRF secrets are returned in cookies while only SHA-256 digests are persisted. Sessions expire after `SESSION_TTL_HOURS` (168 hours by default) and logout revokes the database session. Authentication failures use one generic response. Registration and login are rate-limited through Redis and fail closed if the limiter is unavailable.

The session cookie is HttpOnly and SameSite=Lax. The CSRF cookie is readable by the frontend; every state-changing authenticated endpoint requires its value in `X-CSRF-Token`, and the stored digest is checked in constant time. Cookies are Secure in production. `GET /api/v1/auth/me` returns the current identity. Password reset, email verification, MFA, and session management UI are not implemented yet.
