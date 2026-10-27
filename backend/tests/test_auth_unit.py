import pytest
from pydantic import ValidationError

from app.modules.auth.schemas import Credentials
from app.modules.auth.security import digest_secret, new_secret, secret_matches


def test_credentials_normalize_email_and_reject_weak_password() -> None:
    credentials = Credentials(
        email=" Merchant@Example.Test ", password="correct-horse-battery-staple"
    )
    assert credentials.email == "merchant@example.test"
    with pytest.raises(ValidationError):
        Credentials(email="bad-address", password="short")


def test_session_secret_is_random_and_only_hash_verifies() -> None:
    secret = new_secret()
    assert len(secret) >= 32
    assert digest_secret(secret) != secret
    assert secret_matches(secret, digest_secret(secret))
    assert not secret_matches("other", digest_secret(secret))


def test_rate_limit_rejects_requests_over_the_window(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException
    from starlette.requests import Request

    from app.core import rate_limit
    from tests.conftest import FakeRedis

    store = FakeRedis()
    monkeypatch.setattr(rate_limit, "_redis", lambda: store)
    limit = rate_limit.rate_limit("unit-test", 1, 60)
    request = Request({"type": "http", "client": ("127.0.0.1", 1234)})

    limit(request)
    with pytest.raises(HTTPException) as error:
        limit(request)
    assert error.value.status_code == 429
