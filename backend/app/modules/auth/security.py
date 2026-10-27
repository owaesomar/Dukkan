import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from pwdlib import PasswordHash

_password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return _password_hasher.verify(password, stored_hash)


def new_secret() -> str:
    return secrets.token_urlsafe(32)


def digest_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def secret_matches(secret: str, expected_hash: str) -> bool:
    return hmac.compare_digest(digest_secret(secret), expected_hash)


def session_expiry(hours: int) -> datetime:
    return datetime.now(UTC) + timedelta(hours=hours)
