from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class HistoryRecordOut(BaseModel):
    record_id: str = Field(description="Unique UUID for this prediction record")
    condition: str = Field(description="Condition evaluated: heart or diabetes")
    predicted_label: str = Field(description="Clinical outcome text, e.g. Positive / Negative")
    predicted_positive: bool = Field(description="True if outcome is positive")
    probability: float = Field(description="Primary model or consensus probability score")
    threshold: float = Field(description="Decision threshold")
    aggregation_method: str = Field(description="Method used: majority_voting or single_model")
    model_version: str | None = Field(default=None, description="Model release version identifier")
    is_experimental: bool = Field(description="True if experimental/unvalidated consensus was used")
    model_results: list[dict[str, Any]] | None = Field(
        default=None, description="Detailed results from each candidate model"
    )
    top_factors: list[dict[str, Any]] | None = Field(
        default=None, description="Top influential factors from SHAP explainer"
    )
    input_summary: dict[str, Any] | None = Field(
        default=None, description="Minimal non-sensitive input measurements summary"
    )
    created_at: datetime = Field(description="Timestamp when assessment was performed")

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info: Any) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class HistoryListResponse(BaseModel):
    items: list[HistoryRecordOut]
    total: int
    limit: int
    offset: int


class FactorContribution(BaseModel):
    feature: str
    label: str
    contribution: float
    direction: str
    imputed: bool = False
