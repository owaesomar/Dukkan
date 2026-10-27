from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.rate_limit import rate_limit
from app.db.dependencies import SessionDep
from app.modules.auth.dependencies import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    CsrfPrincipalDep,
    PrincipalDep,
)
from app.modules.auth.schemas import AuthResponse, Credentials
from app.modules.auth.security import (
    digest_secret,
    hash_password,
    new_secret,
    session_expiry,
    verify_password,
)
from app.modules.users.models import AuthSession, User

router = APIRouter(prefix="/auth", tags=["auth"])


def set_session_cookies(
    response: Response, raw_session: str, csrf_token: str, expires_at: datetime
) -> None:
    settings = get_settings()
    max_age = max(0, int((expires_at - datetime.now(UTC)).total_seconds()))
    secure = settings.app_env == "production"
    response.set_cookie(
        SESSION_COOKIE,
        raw_session,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=secure,
        samesite="lax",
        path="/",
    )


def create_auth_session(db: SessionDep, user: User, response: Response) -> None:
    settings = get_settings()
    raw_session = new_secret()
    csrf_token = new_secret()
    expires_at = session_expiry(settings.session_ttl_hours)
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=digest_secret(raw_session),
            csrf_hash=digest_secret(csrf_token),
            expires_at=expires_at,
        )
    )
    db.commit()
    set_session_cookies(response, raw_session, csrf_token, expires_at)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", 10, 3600))],
)
def register(payload: Credentials, response: Response, db: SessionDep) -> User:
    user = User(
        email=str(payload.email).strip().lower(), password_hash=hash_password(payload.password)
    )
    db.add(user)
    try:
        db.flush()
        create_auth_session(db, user, response)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        ) from exc
    return user


@router.post(
    "/login", response_model=AuthResponse, dependencies=[Depends(rate_limit("login", 30, 900))]
)
def login(payload: Credentials, response: Response, db: SessionDep) -> User:
    user = db.scalar(select(User).where(User.email == str(payload.email).strip().lower()))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    create_auth_session(db, user, response)
    return user


@router.get("/me", response_model=AuthResponse)
def me(principal: PrincipalDep) -> User:
    return principal.user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    principal: CsrfPrincipalDep,
    db: SessionDep,
) -> Response:
    principal.session.revoked_at = datetime.now(UTC)
    db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=get_settings().app_env == "production",
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        CSRF_COOKIE,
        path="/",
        secure=get_settings().app_env == "production",
        httponly=False,
        samesite="lax",
    )
    return response
