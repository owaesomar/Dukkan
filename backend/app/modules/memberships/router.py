from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.db.dependencies import SessionDep
from app.modules.auth.dependencies import require_csrf
from app.modules.memberships.authorization import (
    MemberManageDep,
    MemberReadDep,
    can_manage_target,
    lock_store_access,
)
from app.modules.memberships.models import StoreMembership
from app.modules.memberships.schemas import MembershipCreate, MembershipResponse, MembershipUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/stores/{store_id}/members", tags=["memberships"])


def serialize_membership(membership: StoreMembership, user: User) -> MembershipResponse:
    return MembershipResponse(
        store_id=membership.store_id,
        user_id=membership.user_id,
        email=user.email,
        role=membership.role,  # type: ignore[arg-type]
        is_active=membership.is_active,
        created_at=membership.created_at,
    )


@router.get("", response_model=list[MembershipResponse])
def list_members(access: MemberReadDep, db: SessionDep) -> list[MembershipResponse]:
    rows = db.execute(
        select(StoreMembership, User)
        .join(User, User.id == StoreMembership.user_id)
        .where(StoreMembership.store_id == access.store.id)
        .order_by(StoreMembership.created_at)
    ).all()
    return [serialize_membership(membership, user) for membership, user in rows]


@router.post(
    "",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def add_member(
    payload: MembershipCreate,
    db: SessionDep,
    access: MemberManageDep,
) -> MembershipResponse:
    access = lock_store_access(db, access, "members:manage")
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=404, detail="User account not found")
    role = payload.role
    if access.membership.role == "admin" and role in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Admins cannot grant owner or admin access")
    membership = db.get(StoreMembership, (access.store.id, user.id))
    if membership is not None and membership.is_active:
        raise HTTPException(status_code=409, detail="User is already a store member")
    if membership is None:
        membership = StoreMembership(
            store_id=access.store.id,
            user_id=user.id,
            role=role,
            is_active=True,
            created_by_user_id=access.principal.user.id,
        )
        db.add(membership)
    else:
        membership.role = role
        membership.is_active = True
        membership.created_by_user_id = access.principal.user.id
    db.commit()
    db.refresh(membership)
    return serialize_membership(membership, user)


@router.patch("/{user_id}", response_model=MembershipResponse, dependencies=[Depends(require_csrf)])
def update_member(
    user_id: int,
    payload: MembershipUpdate,
    db: SessionDep,
    access: MemberManageDep,
) -> MembershipResponse:
    access = lock_store_access(db, access, "members:manage")
    target = db.get(StoreMembership, (access.store.id, user_id))
    if target is None or not target.is_active:
        raise HTTPException(status_code=404, detail="Store member not found")
    if not can_manage_target(access.membership, target):
        raise HTTPException(status_code=403, detail="Insufficient membership management permission")
    if access.membership.role == "admin" and payload.role in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Admins cannot grant owner or admin access")
    if target.role == "owner" and payload.role != "owner":
        owner_count = db.scalar(
            select(func.count())
            .select_from(StoreMembership)
            .where(
                StoreMembership.store_id == access.store.id,
                StoreMembership.role == "owner",
                StoreMembership.is_active.is_(True),
            )
        )
        if owner_count is not None and owner_count <= 1:
            raise HTTPException(
                status_code=409, detail="A store must retain at least one active owner"
            )
    target.role = payload.role
    db.commit()
    db.refresh(target)
    user = db.get(User, target.user_id)
    assert user is not None
    return serialize_membership(target, user)


@router.delete(
    "/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)]
)
def remove_member(
    user_id: int,
    db: SessionDep,
    access: MemberManageDep,
) -> None:
    access = lock_store_access(db, access, "members:manage")
    target = db.get(StoreMembership, (access.store.id, user_id))
    if target is None or not target.is_active:
        raise HTTPException(status_code=404, detail="Store member not found")
    if not can_manage_target(access.membership, target):
        raise HTTPException(status_code=403, detail="Insufficient membership management permission")
    if target.role == "owner":
        owner_count = db.scalar(
            select(func.count())
            .select_from(StoreMembership)
            .where(
                StoreMembership.store_id == access.store.id,
                StoreMembership.role == "owner",
                StoreMembership.is_active.is_(True),
            )
        )
        if owner_count is not None and owner_count <= 1:
            raise HTTPException(
                status_code=409, detail="A store must retain at least one active owner"
            )
    target.is_active = False
    db.commit()
