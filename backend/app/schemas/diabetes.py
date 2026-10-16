from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.heart import (
    ContributionOut,
    ExplanationOut,
    FeatureImpactOut,
    FeatureSpecOut,
    ModelInfo,
    ModelsResponse,
    SensitivityOut,
)
from ml.pipelines.diabetes import FEATURES, SUSPICIOUS_ZERO_FEATURES

# Safeguard: require at least 5 valid measurements to prevent
# predictions dominated by imputed population medians.
MIN_EFFECTIVE_FEATURES = 5


class DiabetesPatientInput(BaseModel):
    """Measurements for one patient. At least 5 effective measurements required.

    Value codes and units are listed by GET /api/v1/diabetes/features.
    Zeros in plas, pres, skin, insu, mass are unmeasured and do not count.
    """

    model_config = ConfigDict(extra="forbid")

    preg: int | None = Field(default=None, ge=0, le=25, description="Number of pregnancies")
    plas: float | None = Field(
        default=None,
        ge=0.0,
        le=500.0,
        description="Plasma glucose concentration (mg/dL; 0 = unmeasured)",
    )
    pres: float | None = Field(
        default=None,
        ge=0.0,
        le=300.0,
        description="Diastolic blood pressure (mm Hg; 0 = unmeasured)",
    )
    skin: float | None = Field(
        default=None,
        ge=0.0,
        le=120.0,
        description="Triceps skin fold thickness (mm; 0 = unmeasured)",
    )
    insu: float | None = Field(
        default=None,
        ge=0.0,
        le=1000.0,
        description="2-hour serum insulin (mu U/ml; 0 = unmeasured)",
    )
    mass: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Body mass index (kg/m^2; 0 = unmeasured)",
    )
    pedi: float | None = Field(
        default=None, ge=0.0, le=3.5, description="Diabetes pedigree function"
    )
    age: int | None = Field(
        default=None, ge=21, le=120, description="Age in years (cohort inclusion criterion: >= 21)"
    )

    @model_validator(mode="after")
    def require_minimum_effective_measurements(self) -> Self:
        effective = 0
        data = self.model_dump()
        for feature, val in data.items():
            if val is not None:
                if feature in SUSPICIOUS_ZERO_FEATURES and float(val) == 0.0:
                    continue
                effective += 1
        if effective < MIN_EFFECTIVE_FEATURES:
            raise ValueError(
                f"At least {MIN_EFFECTIVE_FEATURES} of {len(FEATURES)} valid measurements are "
                "required (excluding unmeasured zeros in plas, pres, skin, insu, mass); "
                f"{effective} provided."
            )
        return self


class DiabetesPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    model_name: Literal["logistic_regression", "random_forest"] = "logistic_regression"
    patient: DiabetesPatientInput


class DiabetesAgreementOut(BaseModel):
    rank_correlation: float | None = Field(
        description="Spearman rank correlation of feature importance magnitudes"
    )
    top_k_overlap: float = Field(
        description="Share of top-k features identified by both explainers"
    )
    sign_agreement: float = Field(
        description="Share of top-k features with concordant directional signs"
    )
    k: int


class DiabetesPredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    model_version: str
    probability: float = Field(description="Predicted probability of diabetes")
    threshold: float
    predicted_positive: bool
    calibrated: bool
    imputed_features: list[str]
    warnings: list[str]
    shap: ExplanationOut
    lime: ExplanationOut
    agreement: DiabetesAgreementOut | None = Field(
        default=None,
        description="Present when compared explainers evaluate identical output spaces",
    )
    sensitivity: SensitivityOut | None = Field(
        default=None,
        description="Present only when some inputs were missing",
    )
    disclaimer: str


__all__ = [
    "ContributionOut",
    "DiabetesAgreementOut",
    "DiabetesPatientInput",
    "DiabetesPredictionRequest",
    "DiabetesPredictionResponse",
    "ExplanationOut",
    "FeatureImpactOut",
    "FeatureSpecOut",
    "ModelInfo",
    "ModelsResponse",
    "SensitivityOut",
]
