from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.common.exceptions import DomainError
from app.modules.orders.schemas import CheckoutRequest
from app.modules.orders.service import create_cod_order
from tests.conftest import csrf_headers, register


def setup_store(client: TestClient, slug: str, stock: int = 10) -> tuple[int, int, int]:
    register(client, f"{slug}@example.test")
    store_response = client.post(
        "/api/v1/stores",
        json={"name": slug.replace("-", " ").title(), "slug": slug},
        headers=csrf_headers(client),
    )
    assert store_response.status_code == 201, store_response.text
    store_id = store_response.json()["id"]
    product_response = client.post(
        f"/api/v1/stores/{store_id}/products",
        json={"title": "Everyday Backpack", "description": "A durable daily bag."},
        headers=csrf_headers(client),
    )
    assert product_response.status_code == 201, product_response.text
    product_id = product_response.json()["id"]
    variant_response = client.post(
        f"/api/v1/stores/{store_id}/products/{product_id}/variants",
        json={"sku": f"{slug}-bag", "title": "One size", "price_minor": 259900},
        headers=csrf_headers(client),
    )
    assert variant_response.status_code == 201, variant_response.text
    variant_id = variant_response.json()["id"]
    published = client.patch(
        f"/api/v1/stores/{store_id}/products/{product_id}",
        json={"status": "published"},
        headers=csrf_headers(client),
    )
    assert published.status_code == 200, published.text
    adjustment = client.post(
        f"/api/v1/stores/{store_id}/inventory/variants/{variant_id}/adjustments",
        json={"delta": stock, "reason": "Opening stock"},
        headers=csrf_headers(client),
    )
    assert adjustment.status_code == 201, adjustment.text
    return store_id, product_id, variant_id


def checkout_body(variant_id: int, quantity: int = 2) -> dict:
    return {
        "email": "buyer@example.test",
        "full_name": "Example Buyer",
        "phone": "+8801712345678",
        "shipping_address": "12 Example Road, Dhanmondi",
        "city": "Dhaka",
        "postal_code": "1209",
        "country": "BD",
        "items": [{"variant_id": variant_id, "quantity": quantity}],
    }


def test_public_catalog_checkout_idempotency_tracking_and_fulfillment(
    test_client: TestClient,
) -> None:
    merchant = test_client
    store_id, product_id, variant_id = setup_store(merchant, "shop-cod")
    store = merchant.get("/api/v1/public/stores/shop-cod")
    assert store.status_code == 200
    category = merchant.post(
        f"/api/v1/stores/{store_id}/categories",
        json={"name": "Bags", "slug": "bags"},
        headers=csrf_headers(merchant),
    )
    assert category.status_code == 201, category.text
    category_id = category.json()["id"]
    assigned = merchant.patch(
        f"/api/v1/stores/{store_id}/products/{product_id}",
        json={"category_id": category_id},
        headers=csrf_headers(merchant),
    )
    assert assigned.status_code == 200, assigned.text
    public_categories = merchant.get("/api/v1/public/stores/shop-cod/categories")
    assert [item["slug"] for item in public_categories.json()] == ["bags"]
    public_product = merchant.get(f"/api/v1/public/stores/shop-cod/products/{product_id}")
    assert public_product.status_code == 200
    assert public_product.json()["variants"][0]["available_quantity"] == 10
    catalog = merchant.get("/api/v1/public/stores/shop-cod/products")
    assert [item["id"] for item in catalog.json()] == [product_id]
    search = merchant.get("/api/v1/public/stores/shop-cod/products?q=backpack")
    assert [item["id"] for item in search.json()] == [product_id]
    category_filter = merchant.get(
        f"/api/v1/public/stores/shop-cod/products?category_id={category_id}"
    )
    assert [item["id"] for item in category_filter.json()] == [product_id]
    empty_search = merchant.get("/api/v1/public/stores/shop-cod/products?q=not-a-product")
    assert empty_search.json() == []

    hidden_category = merchant.post(
        f"/api/v1/stores/{store_id}/categories",
        json={"name": "Unlisted", "slug": "unlisted"},
        headers=csrf_headers(merchant),
    ).json()
    hidden = merchant.post(
        f"/api/v1/stores/{store_id}/products",
        json={"title": "Not for the public", "category_id": hidden_category["id"]},
        headers=csrf_headers(merchant),
    ).json()
    public_hidden = merchant.get(f"/api/v1/public/stores/shop-cod/products/{hidden['id']}")
    assert public_hidden.status_code == 404
    assert [
        item["slug"] for item in merchant.get("/api/v1/public/stores/shop-cod/categories").json()
    ] == ["bags"]

    key = "cod-checkout-key-0001"
    first = merchant.post(
        "/api/v1/public/stores/shop-cod/checkout",
        json=checkout_body(variant_id),
        headers={"Idempotency-Key": key},
    )
    assert first.status_code == 201, first.text
    first_data = first.json()
    assert first_data["payment_method"] == "cash_on_delivery"
    assert first_data["total_minor"] == 519800
    assert merchant.get(f"/api/v1/stores/{store_id}/inventory").json()[0]["reserved_quantity"] == 2

    replay = merchant.post(
        "/api/v1/public/stores/shop-cod/checkout",
        json=checkout_body(variant_id),
        headers={"Idempotency-Key": key},
    )
    assert replay.status_code == 201, replay.text
    replay_data = replay.json()
    assert replay_data["order_code"] == first_data["order_code"]
    assert replay_data["tracking_token"] != first_data["tracking_token"]
    changed_replay = merchant.post(
        "/api/v1/public/stores/shop-cod/checkout",
        json=checkout_body(variant_id, 1),
        headers={"Idempotency-Key": key},
    )
    assert changed_replay.status_code == 409

    tracked = merchant.get(
        f"/api/v1/public/stores/shop-cod/orders/{replay_data['order_code']}",
        headers={"X-Order-Tracking-Token": replay_data["tracking_token"]},
    )
    assert tracked.status_code == 200
    assert tracked.json()["status"] == "pending"
    assert "customer_email" not in tracked.json()
    invalid_tracking = merchant.get(
        f"/api/v1/public/stores/shop-cod/orders/{replay_data['order_code']}",
        headers={"X-Order-Tracking-Token": "x" * 40},
    )
    assert invalid_tracking.status_code == 404

    merchant_order = merchant.get(f"/api/v1/stores/{store_id}/orders").json()[0]
    order_id = merchant_order["id"]
    assert merchant_order["customer_email"] == "buyer@example.test"
    confirmed = merchant.patch(
        f"/api/v1/stores/{store_id}/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=csrf_headers(merchant),
    )
    assert confirmed.status_code == 200, confirmed.text
    shipped = merchant.patch(
        f"/api/v1/stores/{store_id}/orders/{order_id}/status",
        json={"status": "shipped"},
        headers=csrf_headers(merchant),
    )
    assert shipped.status_code == 200, shipped.text
    inventory = merchant.get(f"/api/v1/stores/{store_id}/inventory").json()[0]
    assert inventory["quantity_on_hand"] == 8
    assert inventory["reserved_quantity"] == 0
    delivered = merchant.patch(
        f"/api/v1/stores/{store_id}/orders/{order_id}/status",
        json={"status": "delivered"},
        headers=csrf_headers(merchant),
    )
    assert delivered.status_code == 200
    assert delivered.json()["payment_status"] == "paid"


def test_cancelled_cod_order_releases_reserved_stock(test_client: TestClient) -> None:
    merchant = test_client
    store_id, _, variant_id = setup_store(merchant, "shop-cancel", stock=4)
    order = merchant.post(
        "/api/v1/public/stores/shop-cancel/checkout",
        json=checkout_body(variant_id, 3),
        headers={"Idempotency-Key": "cancel-checkout-key-001"},
    )
    assert order.status_code == 201, order.text
    order_id = merchant.get(f"/api/v1/stores/{store_id}/orders").json()[0]["id"]
    cancelled = merchant.patch(
        f"/api/v1/stores/{store_id}/orders/{order_id}/status",
        json={"status": "cancelled"},
        headers=csrf_headers(merchant),
    )
    assert cancelled.status_code == 200, cancelled.text
    inventory = merchant.get(f"/api/v1/stores/{store_id}/inventory").json()[0]
    assert inventory["quantity_on_hand"] == 4
    assert inventory["reserved_quantity"] == 0


def test_checkout_headers_are_allowed_by_cors(test_client: TestClient) -> None:
    response = test_client.options(
        "/api/v1/public/stores/shop-cod/checkout",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,idempotency-key",
        },
    )
    assert response.status_code == 200
    assert "idempotency-key" in response.headers["access-control-allow-headers"].lower()


def test_concurrent_checkouts_cannot_oversell_stock(test_client: TestClient, test_engine) -> None:
    merchant = test_client
    _, _, variant_id = setup_store(merchant, "shop-race", stock=5)
    payload = CheckoutRequest.model_validate(checkout_body(variant_id, 4))
    session_factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    barrier = Barrier(2)

    def place_order(key: str) -> str:
        barrier.wait()
        with session_factory() as db:
            try:
                create_cod_order(db, "shop-race", key, payload)
                return "created"
            except DomainError as exc:
                assert exc.status_code == 409
                return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(
            executor.map(place_order, ["race-checkout-key-0001", "race-checkout-key-0002"])
        )
    assert sorted(outcomes) == ["created", "rejected"]
    inventory = merchant.get(f"/api/v1/stores/{_store_id(merchant)}/inventory").json()[0]
    assert inventory["quantity_on_hand"] == 5
    assert inventory["reserved_quantity"] == 4


def test_concurrent_duplicate_checkout_key_creates_one_order(
    test_client: TestClient, test_engine
) -> None:
    merchant = test_client
    store_id, _, variant_id = setup_store(merchant, "shop-idempotent-race", stock=6)
    payload = CheckoutRequest.model_validate(checkout_body(variant_id, 2))
    session_factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    barrier = Barrier(2)

    def place_order(_: int) -> str:
        barrier.wait()
        with session_factory() as db:
            return create_cod_order(
                db, "shop-idempotent-race", "one-shared-idempotency-key", payload
            ).order_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        order_codes = list(executor.map(place_order, range(2)))

    assert order_codes[0] == order_codes[1]
    assert len(merchant.get(f"/api/v1/stores/{store_id}/orders").json()) == 1
    inventory = merchant.get(f"/api/v1/stores/{store_id}/inventory").json()[0]
    assert inventory["reserved_quantity"] == 2


def _store_id(client: TestClient) -> int:
    return client.get("/api/v1/stores").json()[0]["id"]
