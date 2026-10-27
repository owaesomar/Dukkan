from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.integrations.storage import s3
from app.modules.catalog.models import Product, ProductVariant
from tests.conftest import csrf_headers, register


def create_store(client: TestClient, name: str, slug: str) -> int:
    response = client.post(
        "/api/v1/stores",
        json={"name": name, "slug": slug},
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_catalog_is_store_scoped_and_inventory_is_adjusted_transactionally(
    test_client: TestClient, test_engine
) -> None:
    owner_a = test_client
    register(owner_a, "catalog-a@example.test")
    store_a = create_store(owner_a, "Catalog A", "catalog-a")
    category_a = owner_a.post(
        f"/api/v1/stores/{store_a}/categories",
        json={"name": "Clothing", "slug": "clothing"},
        headers=csrf_headers(owner_a),
    ).json()["id"]
    product_a = owner_a.post(
        f"/api/v1/stores/{store_a}/products",
        json={"title": "Blue Shirt", "category_id": category_a},
        headers=csrf_headers(owner_a),
    ).json()["id"]
    assert (
        owner_a.patch(
            f"/api/v1/stores/{store_a}/products/{product_a}",
            json={"status": "published"},
            headers=csrf_headers(owner_a),
        ).status_code
        == 422
    )
    variant_a = owner_a.post(
        f"/api/v1/stores/{store_a}/products/{product_a}/variants",
        json={
            "sku": " shirt-blue-m ",
            "title": "Medium",
            "price_minor": 129900,
            "currency": "BDT",
            "options": {"size": "M", "color": "blue"},
        },
        headers=csrf_headers(owner_a),
    )
    assert variant_a.status_code == 201, variant_a.text
    variant_id = variant_a.json()["id"]
    assert variant_a.json()["sku"] == "SHIRT-BLUE-M"
    assert (
        owner_a.patch(
            f"/api/v1/stores/{store_a}/products/{product_a}",
            json={"status": "published"},
            headers=csrf_headers(owner_a),
        ).status_code
        == 200
    )

    adjustment = owner_a.post(
        f"/api/v1/stores/{store_a}/inventory/variants/{variant_id}/adjustments",
        json={"delta": 5, "reason": "Initial stock"},
        headers=csrf_headers(owner_a),
    )
    assert adjustment.status_code == 201, adjustment.text
    inventory = owner_a.get(f"/api/v1/stores/{store_a}/inventory").json()
    assert inventory[0]["quantity_on_hand"] == 5
    negative = owner_a.post(
        f"/api/v1/stores/{store_a}/inventory/variants/{variant_id}/adjustments",
        json={"delta": -6, "reason": "Invalid stock removal"},
        headers=csrf_headers(owner_a),
    )
    assert negative.status_code == 409
    assert owner_a.get(f"/api/v1/stores/{store_a}/inventory").json()[0]["quantity_on_hand"] == 5

    owner_b = TestClient(owner_a.app)
    register(owner_b, "catalog-b@example.test")
    store_b = create_store(owner_b, "Catalog B", "catalog-b")
    category_b = owner_b.post(
        f"/api/v1/stores/{store_b}/categories",
        json={"name": "Shoes", "slug": "shoes"},
        headers=csrf_headers(owner_b),
    ).json()["id"]
    product_b = owner_b.post(
        f"/api/v1/stores/{store_b}/products",
        json={"title": "Red Shoe", "category_id": category_b},
        headers=csrf_headers(owner_b),
    ).json()["id"]

    assert owner_a.get(f"/api/v1/stores/{store_a}/products/{product_b}").status_code == 404
    assert (
        owner_a.patch(
            f"/api/v1/stores/{store_a}/products/{product_b}",
            json={"title": "Changed"},
            headers=csrf_headers(owner_a),
        ).status_code
        == 404
    )
    assert (
        owner_a.post(
            f"/api/v1/stores/{store_a}/products",
            json={"title": "Cross Store Category", "category_id": category_b},
            headers=csrf_headers(owner_a),
        ).status_code
        == 404
    )

    session_factory = sessionmaker(bind=test_engine)
    with session_factory() as db:
        db.add(Product(store_id=store_a, category_id=category_b, title="Bad cross-store product"))
        try:
            db.commit()
            raise AssertionError("composite category foreign key should reject cross-store linking")
        except IntegrityError:
            db.rollback()
        db.add(
            ProductVariant(
                store_id=store_a,
                product_id=product_b,
                sku="CROSS-STORE-SKU",
                title="Default",
                price_minor=10,
                currency="BDT",
                options={},
            )
        )
        try:
            db.commit()
            raise AssertionError("composite product foreign key should reject cross-store variants")
        except IntegrityError:
            db.rollback()
    owner_b.close()


def test_product_image_upload_checks_content_and_scopes_media(
    test_client: TestClient, monkeypatch
) -> None:
    client = test_client
    register(client, "media-owner@example.test")
    store_id = create_store(client, "Media Store", "media-store")
    product_id = client.post(
        f"/api/v1/stores/{store_id}/products",
        json={"title": "Photo Item"},
        headers=csrf_headers(client),
    ).json()["id"]
    monkeypatch.setattr(
        s3,
        "upload_image",
        lambda store, product, data, content_type, extension: "stores/1/photo.png",
    )
    monkeypatch.setattr(s3, "presigned_get_url", lambda key: "https://storage.example/signed")

    rejected = client.post(
        f"/api/v1/stores/{store_id}/products/{product_id}/media",
        files={"file": ("x.svg", b"<svg onload='alert(1)' />", "image/svg+xml")},
        headers=csrf_headers(client),
    )
    assert rejected.status_code == 415

    uploaded = client.post(
        f"/api/v1/stores/{store_id}/products/{product_id}/media",
        files={
            "file": ("ignored.png", b"\x89PNG\r\n\x1a\nimage-bytes", "application/octet-stream")
        },
        data={"alt_text": "A product image"},
        headers=csrf_headers(client),
    )
    assert uploaded.status_code == 201, uploaded.text
    media_id = uploaded.json()["id"]
    signed_url = client.get(f"/api/v1/stores/{store_id}/products/{product_id}/media/{media_id}/url")
    assert signed_url.json() == {"url": "https://storage.example/signed", "expires_in": 900}


def test_concurrent_stock_decreases_cannot_make_inventory_negative(
    test_client: TestClient, test_engine
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from app.common.exceptions import DomainError
    from app.modules.inventory.schemas import InventoryAdjustmentCreate
    from app.modules.inventory.service import adjust_inventory

    client = test_client
    register(client, "stock-race@example.test")
    store_id = create_store(client, "Race Store", "race-store")
    product_id = client.post(
        f"/api/v1/stores/{store_id}/products",
        json={"title": "Limited Stock"},
        headers=csrf_headers(client),
    ).json()["id"]
    variant_id = client.post(
        f"/api/v1/stores/{store_id}/products/{product_id}/variants",
        json={"sku": "limited-1", "price_minor": 1000},
        headers=csrf_headers(client),
    ).json()["id"]
    actor_user_id = client.get("/api/v1/auth/me").json()["id"]
    client.post(
        f"/api/v1/stores/{store_id}/inventory/variants/{variant_id}/adjustments",
        json={"delta": 5, "reason": "Opening stock"},
        headers=csrf_headers(client),
    )

    session_factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    barrier = Barrier(2)

    def decrease_stock() -> str:
        barrier.wait()
        with session_factory() as db:
            try:
                adjust_inventory(
                    db,
                    store_id,
                    variant_id,
                    actor_user_id,
                    InventoryAdjustmentCreate(delta=-4, reason="Concurrent sale correction"),
                )
                return "adjusted"
            except DomainError as exc:
                assert exc.status_code == 409
                return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: decrease_stock(), range(2)))
    assert sorted(outcomes) == ["adjusted", "rejected"]
    assert client.get(f"/api/v1/stores/{store_id}/inventory").json()[0]["quantity_on_hand"] == 1
