from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from app.db.dependencies import SessionDep
from app.modules.auth.dependencies import Principal, PrincipalDep
from app.modules.platform_admin.models import PlatformAdminRole


def require_platform_admin(principal: PrincipalDep, db: SessionDep) -> Principal:
    grant = db.scalar(
        select(PlatformAdminRole).where(
            PlatformAdminRole.user_id == principal.user.id,
            PlatformAdminRole.is_active.is_(True),
        )
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator access required",
        )
    return principal


PlatformAdminDep = Annotated[Principal, Depends(require_platform_admin)]
