from collections.abc import Callable
from typing import cast

from fastapi import HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

_client: Redis | None = None


def _redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    return _client


def rate_limit(action: str, limit: int, window_seconds: int) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        key = f"dukkan:rate:{action}:{client_host}"
        try:
            client = _redis()
            count = cast(
                int,
                client.eval(
                    "local n=redis.call('INCR',KEYS[1]); "
                    "if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; "
                    "return n",
                    1,
                    key,
                    str(window_seconds),
                ),
            )
        except RedisError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            ) from exc
        if count > limit:
            raise HTTPException(status_code=429, detail="Too many requests")

    return dependency
