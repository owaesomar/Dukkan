from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.stores.models import Store
    from app.modules.users.models import User


class StoreMembership(Base):
    __tablename__ = "store_memberships"
    __table_args__ = (
        CheckConstraint(
            "role IN ('owner', 'admin', 'manager', 'catalog', 'fulfillment', 'staff', 'viewer')",
            name="ck_store_memberships_role",
        ),
        ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    store_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    role: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=true())
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    store: Mapped["Store"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships", foreign_keys=[user_id])
