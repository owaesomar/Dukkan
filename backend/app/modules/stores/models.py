from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.memberships.models import StoreMembership


class Store(Base):
    __tablename__ = "stores"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'suspended', 'disabled')", name="ck_stores_status"),
        CheckConstraint("length(trim(name)) > 0", name="ck_stores_name_nonblank"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(63), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default=text("'active'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    memberships: Mapped[list["StoreMembership"]] = relationship(
        back_populates="store", cascade="all, delete-orphan"
    )
