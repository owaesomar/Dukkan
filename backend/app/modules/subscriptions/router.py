from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.db.dependencies import SessionDep
from app.modules.auth.dependencies import require_csrf
from app.modules.memberships.authorization import SubscriptionManageDep, SubscriptionReadDep
from app.modules.stores.models import Store
from app.modules.subscriptions.models import StoreSubscription, SubscriptionPlan
from app.modules.subscriptions.schemas import (
    PlanResponse,
    SubscriptionCancel,
    SubscriptionChange,
    SubscriptionResponse,
)

router = APIRouter(tags=["subscriptions"])


def serialize_subscription(
    subscription: StoreSubscription, plan: SubscriptionPlan
) -> SubscriptionResponse:
    return SubscriptionResponse(
        store_id=subscription.store_id,
        plan=PlanResponse.model_validate(plan),
        status=subscription.status,  # type: ignore[arg-type]
        cancellation_reason=subscription.cancellation_reason,
        started_at=subscription.started_at,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        updated_at=subscription.updated_at,
    )


@router.get("/subscription-plans", response_model=list[PlanResponse])
def list_available_plans(db: SessionDep) -> list[SubscriptionPlan]:
    return list(
        db.scalars(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active.is_(True))
            .order_by(SubscriptionPlan.price_minor, SubscriptionPlan.id)
        ).all()
    )


@router.get("/stores/{store_id}/subscription", response_model=SubscriptionResponse | None)
def get_store_subscription(
    db: SessionDep, access: SubscriptionReadDep
) -> SubscriptionResponse | None:
    subscription = db.scalar(
        select(StoreSubscription).where(StoreSubscription.store_id == access.store.id)
    )
    if subscription is None:
        return None
    plan = db.get(SubscriptionPlan, subscription.plan_id)
    if plan is None:
        raise HTTPException(status_code=409, detail="Subscription plan is unavailable")
    return serialize_subscription(subscription, plan)


@router.put(
    "/stores/{store_id}/subscription",
    response_model=SubscriptionResponse,
    dependencies=[Depends(require_csrf)],
)
def change_store_subscription(
    payload: SubscriptionChange,
    db: SessionDep,
    access: SubscriptionManageDep,
) -> SubscriptionResponse:
    store = db.scalar(select(Store).where(Store.id == access.store.id).with_for_update())
    if store is None or store.status != "active":
        raise HTTPException(status_code=404, detail="Store not found")
    plan = db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id == payload.plan_id,
            SubscriptionPlan.is_active.is_(True),
        )
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    subscription = db.scalar(
        select(StoreSubscription).where(StoreSubscription.store_id == store.id).with_for_update()
    )
    if subscription is None:
        subscription = StoreSubscription(store_id=store.id, plan_id=plan.id, status="active")
        db.add(subscription)
    else:
        if subscription.status == "canceled":
            subscription.started_at = datetime.now(UTC)
        subscription.plan_id = plan.id
        subscription.status = "active"
        subscription.cancellation_reason = None
        subscription.cancel_at_period_end = False
    db.commit()
    db.refresh(subscription)
    return serialize_subscription(subscription, plan)


@router.post(
    "/stores/{store_id}/subscription/cancel",
    response_model=SubscriptionResponse,
    dependencies=[Depends(require_csrf)],
)
def cancel_store_subscription(
    payload: SubscriptionCancel,
    db: SessionDep,
    access: SubscriptionManageDep,
) -> SubscriptionResponse:
    subscription = db.scalar(
        select(StoreSubscription)
        .where(StoreSubscription.store_id == access.store.id)
        .with_for_update()
    )
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if subscription.status == "canceled":
        plan = db.get(SubscriptionPlan, subscription.plan_id)
        if plan is None:
            raise HTTPException(status_code=409, detail="Subscription plan is unavailable")
        return serialize_subscription(subscription, plan)
    subscription.status = "canceled"
    subscription.cancel_at_period_end = False
    subscription.cancellation_reason = payload.reason.strip()
    db.commit()
    db.refresh(subscription)
    plan = db.get(SubscriptionPlan, subscription.plan_id)
    if plan is None:
        raise HTTPException(status_code=409, detail="Subscription plan is unavailable")
    return serialize_subscription(subscription, plan)
