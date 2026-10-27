from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.modules.platform_admin.models import PlatformAdminRole
from app.modules.stores.models import Store
from tests.conftest import csrf_headers, register
from tests.test_storefront_checkout import checkout_body, setup_store


def test_platform_admin_is_separate_and_manages_plans_and_store_lifecycle(
    test_client: TestClient, test_engine
) -> None:
    client = test_client
    session_factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db:
        existing_stores = db.scalar(select(func.count(Store.id))) or 0
    register(client, "platform-owner@example.test")
    user_id = client.get("/api/v1/auth/me").json()["id"]
    assert client.get("/api/v1/platform-admin/overview").status_code == 403

    with session_factory() as db:
        db.add(PlatformAdminRole(user_id=user_id, granted_by_user_id=user_id))
        db.commit()

    store = client.post(
        "/api/v1/stores",
        json={"name": "Plan Shop", "slug": "plan-shop"},
        headers=csrf_headers(client),
    ).json()
    plan = client.post(
        "/api/v1/platform-admin/plans",
        json={
            "code": "starter-monthly",
            "name": "Starter",
            "price_minor": 1500,
            "currency": "BDT",
            "billing_interval": "monthly",
            "limits": {"products": 25},
        },
        headers=csrf_headers(client),
    )
    assert plan.status_code == 201, plan.text
    subscription = client.put(
        f"/api/v1/stores/{store['id']}/subscription",
        json={"plan_id": plan.json()["id"]},
        headers=csrf_headers(client),
    )
    assert subscription.status_code == 200, subscription.text
    assert subscription.json()["plan"]["code"] == "starter-monthly"

    overview = client.get("/api/v1/platform-admin/overview").json()
    assert overview["stores_count"] == existing_stores + 1
    assert overview["monthly_recurring_revenue_by_currency"] == {"BDT": 1500}
    assert client.get("/api/v1/platform-admin/merchants").json()[0]["email"] == (
        "platform-owner@example.test"
    )
    assert client.get("/api/v1/platform-admin/subscriptions").json()[0]["store_slug"] == (
        "plan-shop"
    )
    platform_stores = client.get("/api/v1/platform-admin/stores").json()
    assert any(item["slug"] == "plan-shop" for item in platform_stores)
    assert client.get("/api/v1/platform-admin/audit-events").json()

    cancelled = client.post(
        f"/api/v1/stores/{store['id']}/subscription/cancel",
        json={"reason": "Merchant requested cancellation"},
        headers=csrf_headers(client),
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "canceled"
    assert cancelled.json()["cancellation_reason"] == "Merchant requested cancellation"

    self_deactivate = client.patch(
        f"/api/v1/platform-admin/merchants/{user_id}/status",
        json={"is_active": False, "reason": "requested test"},
        headers=csrf_headers(client),
    )
    assert self_deactivate.status_code == 409

    with TestClient(client.app) as merchant:
        register(merchant, "suspend-me@example.test")
        target_id = merchant.get("/api/v1/auth/me").json()["id"]
        granted = client.post(
            "/api/v1/platform-admin/admins",
            json={"email": "suspend-me@example.test"},
            headers=csrf_headers(client),
        )
        assert granted.status_code == 201, granted.text
        assert merchant.get("/api/v1/platform-admin/overview").status_code == 200
        revoked = client.delete(
            f"/api/v1/platform-admin/admins/{target_id}",
            headers=csrf_headers(client),
        )
        assert revoked.status_code == 204
        assert merchant.get("/api/v1/platform-admin/overview").status_code == 403
        target_store = merchant.post(
            "/api/v1/stores",
            json={"name": "Suspended Merchant", "slug": "suspended-merchant"},
            headers=csrf_headers(merchant),
        )
        assert target_store.status_code == 201, target_store.text
        deactivated = client.patch(
            f"/api/v1/platform-admin/merchants/{target_id}/status",
            json={"is_active": False, "reason": "trust review"},
            headers=csrf_headers(client),
        )
        assert deactivated.status_code == 200, deactivated.text
        assert merchant.get("/api/v1/auth/me").status_code == 401

    suspended = client.patch(
        f"/api/v1/platform-admin/stores/{store['id']}/status",
        json={"status": "suspended", "reason": "policy review"},
        headers=csrf_headers(client),
    )
    assert suspended.status_code == 200, suspended.text
    assert client.get("/api/v1/public/stores/plan-shop").status_code == 404
    reactivated = client.patch(
        f"/api/v1/platform-admin/stores/{store['id']}/status",
        json={"status": "active", "reason": "review completed"},
        headers=csrf_headers(client),
    )
    assert reactivated.status_code == 200


def test_store_analytics_are_tenant_scoped_and_manager_cannot_change_memberships(
    test_client: TestClient,
) -> None:
    owner = test_client
    store_id, _, variant_id = setup_store(owner, "analytics-shop")
    order = owner.post(
        "/api/v1/public/stores/analytics-shop/checkout",
        json=checkout_body(variant_id, 2),
        headers={"Idempotency-Key": "analytics-order-key-0001"},
    )
    assert order.status_code == 201, order.text
    order_id = owner.get(f"/api/v1/stores/{store_id}/orders").json()[0]["id"]
    for status in ("confirmed", "shipped", "delivered"):
        updated = owner.patch(
            f"/api/v1/stores/{store_id}/orders/{order_id}/status",
            json={"status": status},
            headers=csrf_headers(owner),
        )
        assert updated.status_code == 200, updated.text

    analytics = owner.get(f"/api/v1/stores/{store_id}/analytics/overview")
    assert analytics.status_code == 200, analytics.text
    assert analytics.json()["orders_count"] == 1
    assert analytics.json()["delivered_orders_count"] == 1
    assert analytics.json()["units_sold"] == 2
    assert analytics.json()["paid_revenue_by_currency"] == {"BDT": 519800}

    manager = TestClient(owner.app)
    register(manager, "manager@example.test")
    added = owner.post(
        f"/api/v1/stores/{store_id}/members",
        json={"email": "manager@example.test", "role": "manager"},
        headers=csrf_headers(owner),
    )
    assert added.status_code == 201, added.text
    manager_analytics = manager.get(f"/api/v1/stores/{store_id}/analytics/overview")
    assert manager_analytics.status_code == 200
    managed_request = manager.patch(
        f"/api/v1/stores/{store_id}/members/{added.json()['user_id']}",
        json={"role": "staff"},
        headers=csrf_headers(manager),
    )
    assert managed_request.status_code == 403

    another_store, _, _ = setup_store(owner, "other-analytics")
    outsider = manager.get(f"/api/v1/stores/{another_store}/analytics/overview")
    assert outsider.status_code == 404
