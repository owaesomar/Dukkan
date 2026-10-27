from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.dependencies import SessionDep
from app.modules.auth.dependencies import PrincipalDep, require_csrf
from app.modules.memberships.authorization import StoreManageDep, StoreReadDep
from app.modules.memberships.models import StoreMembership
from app.modules.stores.models import Store
from app.modules.stores.schemas import StoreCreate, StoreResponse, StoreUpdate

router = APIRouter(prefix="/stores", tags=["stores"])


@router.post(
    "",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_store(payload: StoreCreate, principal: PrincipalDep, db: SessionDep) -> Store:
    store = Store(name=payload.name.strip(), slug=payload.slug)
    db.add(store)
    try:
        db.flush()
        db.add(
            StoreMembership(
                store_id=store.id,
                user_id=principal.user.id,
                role="owner",
                is_active=True,
                created_by_user_id=principal.user.id,
            )
        )
        db.commit()
        db.refresh(store)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Store slug is already in use") from exc
    return store


@router.get("", response_model=list[StoreResponse])
def list_stores(principal: PrincipalDep, db: SessionDep) -> list[Store]:
    return list(
        db.scalars(
            select(Store)
            .join(StoreMembership, StoreMembership.store_id == Store.id)
            .where(
                StoreMembership.user_id == principal.user.id,
                StoreMembership.is_active.is_(True),
                Store.status == "active",
            )
            .order_by(Store.id)
        ).all()
    )


@router.get("/{store_id}", response_model=StoreResponse)
def get_store(access: StoreReadDep) -> Store:
    return access.store


@router.patch("/{store_id}", response_model=StoreResponse, dependencies=[Depends(require_csrf)])
def update_store(payload: StoreUpdate, db: SessionDep, access: StoreManageDep) -> Store:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="At least one field is required")
    for key, value in changes.items():
        setattr(access.store, key, value.strip() if isinstance(value, str) else value)
    try:
        db.commit()
        db.refresh(access.store)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Store slug is already in use") from exc
    return access.store
