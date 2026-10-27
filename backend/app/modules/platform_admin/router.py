from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError

from app.db.dependencies import SessionDep
from app.modules.auth.dependencies import require_csrf
from app.modules.memberships.models import StoreMembership
from app.modules.orders.models import Order
from app.modules.platform_admin.dependencies import PlatformAdminDep
from app.modules.platform_admin.models import PlatformAdminRole, PlatformAuditEvent
from app.modules.stores.models import Store
from app.modules.subscriptions.models import StoreSubscription, SubscriptionPlan
from app.modules.subscriptions.schemas import (
    AdminGrantRequest,
    AdminGrantResponse,
    MerchantStatusUpdate,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
    PlatformAuditResponse,
    PlatformMerchantResponse,
    PlatformOverview,
    PlatformStoreResponse,
    PlatformSubscriptionResponse,
    StoreStatusUpdate,
)
from app.modules.users.models import AuthSession, User

router = APIRouter(prefix="/platform-admin", tags=["platform administration"])


def _audit(
    db: SessionDep,
    actor_user_id: int,
    action: str,
    resource_type: str,
    resource_id: int | str,
    details: dict[str, object],
) -> None:
    db.add(
        PlatformAuditEvent(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details,
        )
    )


@router.get("/overview", response_model=PlatformOverview)
def overview(db: SessionDep, _: PlatformAdminDep) -> PlatformOverview:
    store_rows = db.execute(select(Store.status, func.count(Store.id)).group_by(Store.status)).all()
    store_counts = {status: int(count) for status, count in store_rows}
    mrr_rows = cast(
        list[tuple[str, int | None]],
        db.execute(
            select(
                SubscriptionPlan.currency,
                func.sum(
                    case(
                        (
                            SubscriptionPlan.billing_interval == "yearly",
                            SubscriptionPlan.price_minor // 12,
                        ),
                        else_=SubscriptionPlan.price_minor,
                    )
                ),
            )
            .join(StoreSubscription, StoreSubscription.plan_id == SubscriptionPlan.id)
            .where(StoreSubscription.status == "active")
            .group_by(SubscriptionPlan.currency)
        ).all(),
    )
    return PlatformOverview(
        users_count=db.scalar(select(func.count(User.id))) or 0,
        stores_count=sum(store_counts.values()),
        active_stores_count=store_counts.get("active", 0),
        suspended_stores_count=store_counts.get("suspended", 0),
        orders_count=db.scalar(select(func.count(Order.id))) or 0,
        subscriptions_count=db.scalar(select(func.count(StoreSubscription.store_id))) or 0,
        monthly_recurring_revenue_by_currency={
            currency: int(amount or 0) for currency, amount in mrr_rows
        },
    )


@router.get("/merchants", response_model=list[PlatformMerchantResponse])
def list_merchants(
    db: SessionDep,
    _: PlatformAdminDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[PlatformMerchantResponse]:
    rows = db.execute(
        select(User, func.count(func.distinct(StoreMembership.store_id)))
        .join(StoreMembership, StoreMembership.user_id == User.id)
        .where(StoreMembership.role == "owner", StoreMembership.is_active.is_(True))
        .group_by(User.id)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [
        PlatformMerchantResponse(
            user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            stores_count=int(count),
            created_at=user.created_at,
        )
        for user, count in rows
    ]


@router.patch(
    "/merchants/{user_id}/status",
    response_model=PlatformMerchantResponse,
    dependencies=[Depends(require_csrf)],
)
def set_merchant_status(
    user_id: int,
    payload: MerchantStatusUpdate,
    db: SessionDep,
    actor: PlatformAdminDep,
) -> PlatformMerchantResponse:
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(status_code=404, detail="Merchant not found")
    previous = user.is_active
    if user.id == actor.user.id and not payload.is_active:
        raise HTTPException(status_code=409, detail="You cannot deactivate your own account")
    user.is_active = payload.is_active
    if not payload.is_active:
        db.query(AuthSession).filter(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None),
        ).update({AuthSession.revoked_at: datetime.now(UTC)}, synchronize_session=False)
    _audit(
        db,
        actor.user.id,
        "merchant.status_changed",
        "user",
        user.id,
        {"from": previous, "to": payload.is_active, "reason": payload.reason.strip()},
    )
    db.commit()
    store_count = (
        db.scalar(
            select(func.count(func.distinct(StoreMembership.store_id))).where(
                StoreMembership.user_id == user.id,
                StoreMembership.role == "owner",
                StoreMembership.is_active.is_(True),
            )
        )
        or 0
    )
    return PlatformMerchantResponse(
        user_id=user.id,
        email=user.email,
        is_active=user.is_active,
        stores_count=store_count,
        created_at=user.created_at,
    )


@router.get("/stores", response_model=list[PlatformStoreResponse])
def list_platform_stores(
    db: SessionDep,
    _: PlatformAdminDep,
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[PlatformStoreResponse]:
    query = (
        select(
            Store,
            func.min(case((StoreMembership.role == "owner", User.email), else_=None)),
            func.count(
                func.distinct(
                    case((StoreMembership.is_active.is_(True), StoreMembership.user_id), else_=None)
                )
            ),
        )
        .outerjoin(StoreMembership, StoreMembership.store_id == Store.id)
        .outerjoin(User, User.id == StoreMembership.user_id)
        .group_by(Store.id)
    )
    if status_filter is not None:
        if status_filter not in {"active", "suspended", "disabled"}:
            raise HTTPException(status_code=422, detail="Invalid store status")
        query = query.where(Store.status == status_filter)
    rows = cast(
        list[tuple[Store, str | None, int]],
        db.execute(query.order_by(Store.created_at.desc()).offset(offset).limit(limit)).all(),
    )
    return [
        PlatformStoreResponse(
            id=store.id,
            name=store.name,
            slug=store.slug,
            status=store.status,  # type: ignore[arg-type]
            created_at=store.created_at,
            owner_email=owner_email,
            members_count=int(members_count),
        )
        for store, owner_email, members_count in rows
    ]


@router.patch(
    "/stores/{store_id}/status",
    response_model=PlatformStoreResponse,
    dependencies=[Depends(require_csrf)],
)
def set_store_status(
    store_id: int,
    payload: StoreStatusUpdate,
    db: SessionDep,
    actor: PlatformAdminDep,
) -> PlatformStoreResponse:
    store = db.scalar(select(Store).where(Store.id == store_id).with_for_update())
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    previous = store.status
    store.status = payload.status
    _audit(
        db,
        actor.user.id,
        "store.status_changed",
        "store",
        store.id,
        {"from": previous, "to": payload.status, "reason": payload.reason.strip()},
    )
    db.commit()
    rows = db.execute(
        select(
            func.min(case((StoreMembership.role == "owner", User.email), else_=None)),
            func.count(
                func.distinct(
                    case((StoreMembership.is_active.is_(True), StoreMembership.user_id), else_=None)
                )
            ),
        )
        .select_from(Store)
        .outerjoin(StoreMembership, StoreMembership.store_id == Store.id)
        .outerjoin(User, User.id == StoreMembership.user_id)
        .where(Store.id == store.id)
    ).one()
    return PlatformStoreResponse(
        id=store.id,
        name=store.name,
        slug=store.slug,
        status=store.status,  # type: ignore[arg-type]
        created_at=store.created_at,
        owner_email=rows[0],
        members_count=int(rows[1]),
    )


@router.get("/plans", response_model=list[PlanResponse])
def list_plans(db: SessionDep, _: PlatformAdminDep) -> list[SubscriptionPlan]:
    return list(db.scalars(select(SubscriptionPlan).order_by(SubscriptionPlan.id)).all())


@router.get("/subscriptions", response_model=list[PlatformSubscriptionResponse])
def list_platform_subscriptions(
    db: SessionDep,
    _: PlatformAdminDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[PlatformSubscriptionResponse]:
    rows = db.execute(
        select(StoreSubscription, Store, SubscriptionPlan)
        .join(Store, Store.id == StoreSubscription.store_id)
        .join(SubscriptionPlan, SubscriptionPlan.id == StoreSubscription.plan_id)
        .order_by(StoreSubscription.started_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [
        PlatformSubscriptionResponse(
            store_id=subscription.store_id,
            store_name=store.name,
            store_slug=store.slug,
            plan_id=plan.id,
            plan_code=plan.code,
            plan_name=plan.name,
            price_minor=plan.price_minor,
            currency=plan.currency,
            billing_interval=plan.billing_interval,  # type: ignore[arg-type]
            status=subscription.status,  # type: ignore[arg-type]
            cancellation_reason=subscription.cancellation_reason,
            started_at=subscription.started_at,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )
        for subscription, store, plan in rows
    ]


@router.post(
    "/plans",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_plan(payload: PlanCreate, db: SessionDep, actor: PlatformAdminDep) -> SubscriptionPlan:
    plan = SubscriptionPlan(**payload.model_dump())
    db.add(plan)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Plan code is already in use") from exc
    _audit(db, actor.user.id, "plan.created", "subscription_plan", plan.id, {"code": plan.code})
    db.commit()
    db.refresh(plan)
    return plan


@router.patch(
    "/plans/{plan_id}",
    response_model=PlanResponse,
    dependencies=[Depends(require_csrf)],
)
def update_plan(
    plan_id: int,
    payload: PlanUpdate,
    db: SessionDep,
    actor: PlatformAdminDep,
) -> SubscriptionPlan:
    plan = db.scalar(
        select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id).with_for_update()
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="At least one plan field is required")
    for key, value in changes.items():
        if value is None and key != "description":
            raise HTTPException(status_code=422, detail=f"{key} cannot be null")
        setattr(plan, key, value)
    _audit(db, actor.user.id, "plan.updated", "subscription_plan", plan.id, changes)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Plan update conflicts with existing data"
        ) from exc
    db.refresh(plan)
    return plan


@router.get("/audit-events", response_model=list[PlatformAuditResponse])
def list_audit_events(
    db: SessionDep,
    _: PlatformAdminDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[PlatformAuditEvent]:
    return list(
        db.scalars(
            select(PlatformAuditEvent)
            .order_by(PlatformAuditEvent.created_at.desc(), PlatformAuditEvent.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )


@router.get("/admins", response_model=list[AdminGrantResponse])
def list_admins(db: SessionDep, _: PlatformAdminDep) -> list[AdminGrantResponse]:
    rows = db.execute(
        select(PlatformAdminRole, User)
        .join(User, User.id == PlatformAdminRole.user_id)
        .where(PlatformAdminRole.is_active.is_(True))
        .order_by(PlatformAdminRole.created_at)
    ).all()
    return [
        AdminGrantResponse(
            user_id=user.id,
            email=user.email,
            is_active=grant.is_active,
            created_at=grant.created_at,
        )
        for grant, user in rows
    ]


@router.post(
    "/admins",
    response_model=AdminGrantResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def grant_admin(
    payload: AdminGrantRequest, db: SessionDep, actor: PlatformAdminDep
) -> AdminGrantResponse:
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if user is None:
        raise HTTPException(status_code=404, detail="User account not found")
    grant = db.get(PlatformAdminRole, user.id)
    if grant is None:
        grant = PlatformAdminRole(user_id=user.id, granted_by_user_id=actor.user.id)
        db.add(grant)
    else:
        grant.is_active = True
        grant.granted_by_user_id = actor.user.id
    _audit(db, actor.user.id, "platform_admin.granted", "user", user.id, {"email": user.email})
    db.commit()
    db.refresh(grant)
    return AdminGrantResponse(
        user_id=user.id, email=user.email, is_active=True, created_at=grant.created_at
    )


@router.delete(
    "/admins/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def revoke_admin(user_id: int, db: SessionDep, actor: PlatformAdminDep) -> None:
    grant = db.scalar(
        select(PlatformAdminRole).where(PlatformAdminRole.user_id == user_id).with_for_update()
    )
    if grant is None or not grant.is_active:
        raise HTTPException(status_code=404, detail="Platform admin grant not found")
    if user_id == actor.user.id:
        raise HTTPException(
            status_code=409, detail="Use another platform administrator to revoke yourself"
        )
    active_grants = list(
        db.scalars(
            select(PlatformAdminRole).where(PlatformAdminRole.is_active.is_(True)).with_for_update()
        ).all()
    )
    if len(active_grants) <= 1:
        raise HTTPException(
            status_code=409, detail="At least one platform administrator must remain"
        )
    grant.is_active = False
    _audit(db, actor.user.id, "platform_admin.revoked", "user", user_id, {})
    db.commit()
