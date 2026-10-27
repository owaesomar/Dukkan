"""Add a few local-only Dukkan shops with sample products for storefront previews."""

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.modules.auth.security import hash_password
from app.modules.catalog.models import Category, Product, ProductVariant
from app.modules.inventory.models import Inventory, InventoryAdjustment
from app.modules.memberships.models import StoreMembership
from app.modules.stores.models import Store
from app.modules.users.models import User

DEMO_PASSWORD = "DukkanDemo-2026!"

SHOPS = [
    {
        "name": "Bay Leaf Pantry",
        "slug": "bay-leaf-pantry",
        "email": "owner@bayleaf.example.test",
        "category": ("Pantry", "pantry"),
        "products": [
            ("Sylhet Seven Spice", "A bright, aromatic blend for everyday curries and roasted vegetables.", "BLP-SPICE-01", 48000, 32),
            ("Green Mango Achar", "Small-batch green mango pickle with mustard, chili, and a little sweetness.", "BLP-ACHAR-01", 62000, 18),
            ("Cold-Pressed Mustard Oil", "Golden, pungent mustard oil pressed in small batches.", "BLP-OIL-01", 85000, 24),
            ("Tea Garden Masala Chai", "Black tea with cardamom, cinnamon, ginger, and clove.", "BLP-TEA-01", 39000, 40),
        ],
    },
    {
        "name": "Loom & Lilt",
        "slug": "loom-and-lilt",
        "email": "owner@loomlilt.example.test",
        "category": ("Handwoven", "handwoven"),
        "products": [
            ("Soft Muslin Wrap", "Lightweight cotton muslin woven for easy, year-round layering.", "LL-WRAP-01", 145000, 12),
            ("Jamdani Everyday Tote", "A sturdy cotton tote with a handwoven Jamdani-inspired panel.", "LL-TOTE-01", 98000, 16),
            ("Kantha Weekend Throw", "A one-of-a-kind patchwork throw made from soft cotton layers.", "LL-THROW-01", 265000, 7),
            ("Indigo Cotton Scarf", "Naturally dyed cotton with a relaxed drape and subtle texture.", "LL-SCARF-01", 112000, 20),
        ],
    },
    {
        "name": "Clay & Kin",
        "slug": "clay-and-kin",
        "email": "owner@claykin.example.test",
        "category": ("Ceramics", "ceramics"),
        "products": [
            ("Riverstone Coffee Cup", "A hand-finished stoneware cup with a warm, speckled glaze.", "CK-CUP-01", 78000, 14),
            ("Sunday Breakfast Bowl", "A generous everyday bowl, shaped and glazed by hand.", "CK-BOWL-01", 125000, 10),
            ("Little Wildflower Vase", "A sculptural bud vase for a single stem or a small bunch.", "CK-VASE-01", 95000, 8),
            ("Soft Dawn Incense Dish", "A small ceramic dish with a smooth matte finish.", "CK-DISH-01", 54000, 18),
        ],
    },
    {
        "name": "Paper Trail Studio",
        "slug": "paper-trail-studio",
        "email": "owner@papertrail.example.test",
        "category": ("Stationery", "stationery"),
        "products": [
            ("Forest Block-Print Journal", "A clothbound journal finished with a hand-printed botanical pattern.", "PTS-JOURNAL-01", 72000, 24),
            ("Quiet Correspondence Set", "Smooth ivory writing paper and envelopes for thoughtful notes.", "PTS-LETTER-01", 56000, 30),
            ("Recycled Gift Wrap", "Textured kraft wrapping paper finished with cotton twine.", "PTS-WRAP-01", 38000, 28),
            ("Wildflower Note Cards", "A set of blank cards with delicate botanical artwork.", "PTS-CARDS-01", 44000, 35),
        ],
    },
    {
        "name": "Orchard & Bloom",
        "slug": "orchard-and-bloom",
        "email": "owner@orchardbloom.example.test",
        "category": ("Garden and flowers", "garden-flowers"),
        "products": [
            ("Sunroom Mini Bouquet", "A seasonal bunch of cheerful yellow and white flowers.", "OB-BOUQUET-01", 88000, 12),
            ("Meadow-Dried Flowers", "A naturally dried bunch of grasses and meadow blooms.", "OB-DRIED-01", 112000, 16),
            ("Balcony Herb Planter", "A terracotta pot planted with fragrant, ready-to-pick basil.", "OB-HERB-01", 98000, 10),
            ("Pollinator Seed Kit", "Easy-to-grow flower seeds selected for small gardens and balconies.", "OB-SEEDS-01", 52000, 26),
        ],
    },
    {
        "name": "Lightwell Home",
        "slug": "lightwell-home",
        "email": "owner@lightwell.example.test",
        "category": ("Home comforts", "home-comforts"),
        "products": [
            ("Amber Hour Candle", "A softly scented candle poured into reusable amber glass.", "LH-CANDLE-01", 105000, 20),
            ("Cloud Linen Cushion Cover", "A relaxed natural-linen cover with a soft, lived-in texture.", "LH-CUSHION-01", 155000, 14),
            ("Brass Dew Incense Holder", "A solid brass holder with a simple, sculptural shape.", "LH-INCENSE-01", 84000, 18),
            ("Woven Everyday Runner", "A handwoven cotton table runner for everyday meals.", "LH-RUNNER-01", 132000, 11),
        ],
    },
]


def get_or_create_owner(db, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password(DEMO_PASSWORD))
        db.add(user)
        db.flush()
    return user


def seed_shop(db, spec: dict[str, object]) -> tuple[str, int, int]:
    owner = get_or_create_owner(db, str(spec["email"]))
    store = db.scalar(select(Store).where(Store.slug == spec["slug"]))
    if store is None:
        store = Store(name=str(spec["name"]), slug=str(spec["slug"]), status="active")
        db.add(store)
        db.flush()
        db.add(
            StoreMembership(
                store_id=store.id,
                user_id=owner.id,
                role="owner",
                is_active=True,
                created_by_user_id=owner.id,
            )
        )
        db.flush()
    elif db.get(StoreMembership, (store.id, owner.id)) is None:
        raise RuntimeError(f"Store slug {store.slug!r} already belongs to another account")

    category_name, category_slug = spec["category"]  # type: ignore[misc]
    category = db.scalar(
        select(Category).where(Category.store_id == store.id, Category.slug == category_slug)
    )
    if category is None:
        category = Category(
            store_id=store.id,
            name=category_name,
            slug=category_slug,
            description=f"Thoughtfully chosen {category_name.lower()} from {store.name}.",
        )
        db.add(category)
        db.flush()

    products_added = 0
    for title, description, sku, price_minor, quantity in spec["products"]:  # type: ignore[union-attr]
        product = db.scalar(
            select(Product).where(Product.store_id == store.id, Product.title == title)
        )
        if product is None:
            product = Product(
                store_id=store.id,
                category_id=category.id,
                title=title,
                description=description,
                status="published",
            )
            db.add(product)
            db.flush()
            variant = ProductVariant(
                store_id=store.id,
                product_id=product.id,
                sku=sku,
                title="Default",
                price_minor=price_minor,
                currency="BDT",
                options={},
            )
            db.add(variant)
            db.flush()
            db.add(
                Inventory(
                    store_id=store.id,
                    variant_id=variant.id,
                    quantity_on_hand=quantity,
                    reserved_quantity=0,
                )
            )
            db.add(
                InventoryAdjustment(
                    store_id=store.id,
                    variant_id=variant.id,
                    actor_user_id=owner.id,
                    delta=quantity,
                    reason="Initial demo storefront stock",
                )
            )
            products_added += 1

    return store.slug, len(spec["products"]), products_added  # type: ignore[arg-type]


def main() -> None:
    if get_settings().app_env != "development":
        raise SystemExit("Demo stores can only be seeded when APP_ENV=development")
    with SessionLocal() as db:
        results = [seed_shop(db, spec) for spec in SHOPS]
        db.commit()
    for spec, (slug, product_count, added_count) in zip(SHOPS, results, strict=True):
        print(
            f"/s/{slug}: {product_count} sample products ({added_count} added this run); "
            f"merchant login {spec['email']}"
        )
    print(f"Demo merchant accounts use the shared local password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
