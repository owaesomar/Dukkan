from fastapi import APIRouter, Depends, status

from app.db.dependencies import SessionDep
from app.modules.auth.dependencies import require_csrf
from app.modules.inventory import service
from app.modules.inventory.schemas import (
    InventoryAdjustmentCreate,
    InventoryAdjustmentResponse,
    InventoryResponse,
)
from app.modules.memberships.authorization import InventoryAdjustDep, InventoryReadDep

router = APIRouter(prefix="/stores/{store_id}/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryResponse])
def list_inventory(db: SessionDep, access: InventoryReadDep) -> list[InventoryResponse]:
    return service.list_inventory(db, access.store.id)


@router.post(
    "/variants/{variant_id}/adjustments",
    response_model=InventoryAdjustmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def adjust_inventory(
    variant_id: int,
    payload: InventoryAdjustmentCreate,
    db: SessionDep,
    access: InventoryAdjustDep,
) -> InventoryAdjustmentResponse:
    _, adjustment = service.adjust_inventory(
        db,
        access.store.id,
        variant_id,
        access.principal.user.id,
        payload,
    )
    return InventoryAdjustmentResponse.model_validate(adjustment)
