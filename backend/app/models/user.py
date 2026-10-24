from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    RESEARCHER = "researcher"
    PATIENT = "patient"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    hashed_password: Mapped[str] = mapped_column(String(255))
    # Stored as VARCHAR (not native ENUM) so adding roles never needs an ALTER ENUM.
    # No default on purpose: a role must always be assigned explicitly.
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            native_enum=False,
            length=20,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda roles: [role.value for role in roles],
        )
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    predictions: Mapped[list[PredictionHistory]] = relationship(
        "PredictionHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"


if TYPE_CHECKING:
    from app.models.prediction_history import PredictionHistory
