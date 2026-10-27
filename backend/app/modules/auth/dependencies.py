from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select

from app.db.dependencies import SessionDep
from app.modules.auth.security import digest_secret, secret_matches
from app.modules.users.models import AuthSession, User

SESSION_COOKIE = "dukkan_session"
CSRF_COOKIE = "dukkan_csrf"


@dataclass(frozen=True)
class Principal:
    user: User
    session: AuthSession


def get_principal(request: Request, db: SessionDep) -> Principal:
    raw_session = request.cookies.get(SESSION_COOKIE)
    if not raw_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == digest_secret(raw_session),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
        )
    )
    if session is None or not session.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return Principal(user=session.user, session=session)


PrincipalDep = Annotated[Principal, Depends(get_principal)]


def require_csrf(request: Request, principal: PrincipalDep) -> Principal:
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if (
        not cookie_token
        or not header_token
        or not hmac_compare(cookie_token, header_token)
        or not secret_matches(cookie_token, principal.session.csrf_hash)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    return principal


CsrfPrincipalDep = Annotated[Principal, Depends(require_csrf)]


def hmac_compare(left: str, right: str) -> bool:
    import hmac

    return hmac.compare_digest(left, right)
