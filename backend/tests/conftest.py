import os
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.dependencies import get_db
from app.main import app
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.customers import models as customers_models  # noqa: F401
from app.modules.inventory import models as inventory_models  # noqa: F401
from app.modules.memberships import models as memberships_models  # noqa: F401
from app.modules.orders import models as orders_models  # noqa: F401
from app.modules.platform_admin import models as platform_admin_models  # noqa: F401
from app.modules.stores import models as stores_models  # noqa: F401
from app.modules.subscriptions import models as subscription_models  # noqa: F401
from app.modules.users import models as users_models  # noqa: F401


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def expire(self, key: str, seconds: int) -> bool:
        return key in self.values

    def ping(self) -> bool:
        return True

    def eval(self, script: str, key_count: int, key: str, seconds: str) -> int:
        return self.incr(key)


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Any]:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated PostgreSQL database ending in _test")
    if not (make_url(url).database or "").endswith("_test"):
        pytest.fail("Refusing to reset TEST_DATABASE_URL unless its database name ends with _test")
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    engine.dispose()


@pytest.fixture
def test_client(test_engine: Any, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    from app.core import rate_limit

    fake_redis = FakeRedis()
    monkeypatch.setattr(rate_limit, "_redis", lambda: fake_redis)
    session_factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get("dukkan_csrf")
    assert token
    return {"X-CSRF-Token": token}


def register(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 201, response.text
