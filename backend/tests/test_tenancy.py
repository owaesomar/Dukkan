from fastapi.testclient import TestClient

from tests.conftest import csrf_headers, register


def create_store(client: TestClient, name: str, slug: str) -> int:
    response = client.post(
        "/api/v1/stores",
        json={"name": name, "slug": slug},
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_cross_tenant_store_access_is_denied(test_client: TestClient) -> None:
    merchant_a = test_client
    register(merchant_a, "merchant-a@example.test")
    store_a = create_store(merchant_a, "Store A", "store-a")
    second_store_a = create_store(merchant_a, "Store A2", "store-a-two")

    merchant_b = TestClient(merchant_a.app)
    register(merchant_b, "merchant-b@example.test")
    store_b = create_store(merchant_b, "Store B", "store-b")

    assert merchant_a.get(f"/api/v1/stores/{store_a}").status_code == 200
    assert merchant_a.get(f"/api/v1/stores/{store_b}").status_code == 404
    assert (
        merchant_a.patch(
            f"/api/v1/stores/{store_b}",
            json={"name": "Hijacked"},
            headers=csrf_headers(merchant_a),
        ).status_code
        == 404
    )
    assert [store["id"] for store in merchant_a.get("/api/v1/stores").json()] == [
        store_a,
        second_store_a,
    ]

    merchant_b.close()


def test_membership_roles_and_owner_invariant(test_client: TestClient) -> None:
    owner = test_client
    register(owner, "owner@example.test")
    store_id = create_store(owner, "Owner Store", "owner-store")

    viewer = TestClient(owner.app)
    register(viewer, "viewer@example.test")
    added = owner.post(
        f"/api/v1/stores/{store_id}/members",
        json={"email": "viewer@example.test", "role": "viewer"},
        headers=csrf_headers(owner),
    )
    assert added.status_code == 201, added.text
    assert viewer.get(f"/api/v1/stores/{store_id}").status_code == 200
    assert (
        viewer.patch(
            f"/api/v1/stores/{store_id}",
            json={"name": "Unauthorized"},
            headers=csrf_headers(viewer),
        ).status_code
        == 403
    )
    assert viewer.get(f"/api/v1/stores/{store_id}/members").status_code == 403

    owner_removal = owner.delete(
        f"/api/v1/stores/{store_id}/members/{owner.get('/api/v1/auth/me').json()['id']}",
        headers=csrf_headers(owner),
    )
    assert owner_removal.status_code == 409
    viewer.close()


def test_mutations_require_csrf_and_logout_revokes_session(test_client: TestClient) -> None:
    client = test_client
    register(client, "csrf@example.test")
    no_csrf = client.post("/api/v1/stores", json={"name": "Bad", "slug": "bad-store"})
    assert no_csrf.status_code == 403

    response = client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_creates_a_revocable_session(test_client: TestClient) -> None:
    client = test_client
    register(client, "login@example.test")
    client.close()

    logged_in = TestClient(client.app)
    response = logged_in.post(
        "/api/v1/auth/login",
        json={"email": "login@example.test", "password": "wrong-password-long"},
    )
    assert response.status_code == 401
    response = logged_in.post(
        "/api/v1/auth/login",
        json={"email": "login@example.test", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 200
    assert logged_in.get("/api/v1/auth/me").status_code == 200
    logged_in.close()


def test_validation_errors_do_not_echo_passwords(test_client: TestClient) -> None:
    response = test_client.post(
        "/api/v1/auth/register",
        json={"email": "invalid@example.test", "password": "sensitive"},
    )
    assert response.status_code == 422
    assert "sensitive" not in response.text
