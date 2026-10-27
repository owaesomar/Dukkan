from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import SessionDep
from app.modules.auth.dependencies import Principal, PrincipalDep
from app.modules.memberships.models import StoreMembership
from app.modules.stores.models import Store

_FULL_STORE_PERMISSIONS = frozenset(
    {
        "store:read",
        "store:manage",
        "members:read",
        "members:manage",
        "catalog:read",
        "catalog:write",
        "inventory:read",
        "inventory:adjust",
        "orders:read",
        "orders:fulfill",
        "subscription:read",
        "subscription:manage",
    }
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "owner": _FULL_STORE_PERMISSIONS,
    "admin": _FULL_STORE_PERMISSIONS,
    "manager": frozenset(
        {
            "store:read",
            "members:read",
            "catalog:read",
            "catalog:write",
            "inventory:read",
            "inventory:adjust",
            "orders:read",
            "orders:fulfill",
            "subscription:read",
        }
    ),
    "catalog": frozenset(
        {"store:read", "catalog:read", "catalog:write", "inventory:read", "inventory:adjust"}
    ),
    "fulfillment": frozenset({"store:read", "inventory:read", "orders:read", "orders:fulfill"}),
    "staff": frozenset({"store:read", "orders:read", "orders:fulfill"}),
    "viewer": frozenset({"store:read", "catalog:read", "inventory:read", "orders:read"}),
}


@dataclass(frozen=True)
class StoreAccess:
    store: Store
    membership: StoreMembership
    principal: Principal


def require_store_permission(permission: str) -> Callable[..., StoreAccess]:
    def dependency(
        store_id: int,
        principal: PrincipalDep,
        db: SessionDep,
    ) -> StoreAccess:
        store = db.get(Store, store_id)
        if store is None or store.status != "active":
            raise HTTPException(status_code=404, detail="Store not found")
        membership = db.scalar(
            select(StoreMembership).where(
                StoreMembership.store_id == store_id,
                StoreMembership.user_id == principal.user.id,
                StoreMembership.is_active.is_(True),
            )
        )
        if membership is None:
            raise HTTPException(status_code=404, detail="Store not found")
        if permission not in ROLE_PERMISSIONS.get(membership.role, frozenset()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient store permission"
            )
        return StoreAccess(store, membership, principal)

    return dependency


StoreReadDep = Annotated[StoreAccess, Depends(require_store_permission("store:read"))]
StoreManageDep = Annotated[StoreAccess, Depends(require_store_permission("store:manage"))]
MemberReadDep = Annotated[StoreAccess, Depends(require_store_permission("members:read"))]
MemberManageDep = Annotated[StoreAccess, Depends(require_store_permission("members:manage"))]
CatalogReadDep = Annotated[StoreAccess, Depends(require_store_permission("catalog:read"))]
CatalogWriteDep = Annotated[StoreAccess, Depends(require_store_permission("catalog:write"))]
InventoryReadDep = Annotated[StoreAccess, Depends(require_store_permission("inventory:read"))]
InventoryAdjustDep = Annotated[StoreAccess, Depends(require_store_permission("inventory:adjust"))]
OrdersReadDep = Annotated[StoreAccess, Depends(require_store_permission("orders:read"))]
OrdersFulfillDep = Annotated[StoreAccess, Depends(require_store_permission("orders:fulfill"))]
SubscriptionReadDep = Annotated[StoreAccess, Depends(require_store_permission("subscription:read"))]
SubscriptionManageDep = Annotated[
    StoreAccess, Depends(require_store_permission("subscription:manage"))
]


def can_manage_target(actor: StoreMembership, target: StoreMembership) -> bool:
    if actor.role == "owner":
        return True
    return actor.role == "admin" and target.role not in {"owner", "admin"}


def lock_store_access(db: Session, access: StoreAccess, permission: str) -> StoreAccess:
    store = db.scalar(select(Store).where(Store.id == access.store.id).with_for_update())
    if store is None or store.status != "active":
        raise HTTPException(status_code=404, detail="Store not found")
    membership = db.scalar(
        select(StoreMembership)
        .where(
            StoreMembership.store_id == store.id,
            StoreMembership.user_id == access.principal.user.id,
            StoreMembership.is_active.is_(True),
        )
        .with_for_update()
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Store not found")
    if permission not in ROLE_PERMISSIONS.get(membership.role, frozenset()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient store permission"
        )
    return StoreAccess(store, membership, access.principal)
