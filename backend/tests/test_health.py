from fastapi.testclient import TestClient

from app.main import app


def test_liveness_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


def test_caller_request_id_is_returned() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live", headers={"X-Request-ID": "release-check-7"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "release-check-7"


def test_readiness_checks_database_and_redis(test_client: TestClient) -> None:
    response = test_client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
