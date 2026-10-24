from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class PredictionHistory(TimestampMixin, Base):
    """Persisted prediction record belonging to an authenticated user."""

    __tablename__ = "prediction_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    condition: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    predicted_label: Mapped[str] = mapped_column(String(50), nullable=False)
    predicted_positive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    aggregation_method: Mapped[str] = mapped_column(
        String(50), default="majority_voting", nullable=False
    )
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    is_experimental: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    model_results: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    top_factors: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    input_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="predictions")

    def __repr__(self) -> str:
        return (
            f"<PredictionHistory id={self.id} record_id={self.record_id!r} "
            f"condition={self.condition!r} user_id={self.user_id}>"
        )
