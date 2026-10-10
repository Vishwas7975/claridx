from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ml.pipelines.heart import FEATURES

# Safety rule: a prediction from a handful of values would be meaningless.
MIN_PROVIDED_FEATURES = 7


class PatientInput(BaseModel):
    """Measurements for one patient. Every field is optional, but at least 7 are required.

    Value codes and labels are listed by GET /api/v1/heart/features.
    """

    model_config = ConfigDict(extra="forbid")

    age: int | None = Field(default=None, ge=18, le=120, description="Age in years")
    sex: Literal[0, 1] | None = Field(default=None, description="0 = female, 1 = male")
    cp: Literal[1, 2, 3, 4] | None = Field(default=None, description="Chest pain type (1 to 4)")
    trestbps: int | None = Field(
        default=None, ge=50, le=300, description="Resting blood pressure, mm Hg"
    )
    chol: int | None = Field(default=None, ge=50, le=700, description="Serum cholesterol, mg/dl")
    fbs: Literal[0, 1] | None = Field(default=None, description="1 = fasting blood sugar > 120")
    restecg: Literal[0, 1, 2] | None = Field(default=None, description="Resting ECG result")
    thalach: int | None = Field(
        default=None, ge=40, le=250, description="Maximum heart rate achieved, bpm"
    )
    exang: Literal[0, 1] | None = Field(default=None, description="1 = exercise-induced angina")
    oldpeak: float | None = Field(
        default=None, ge=0, le=10, description="ST depression induced by exercise"
    )
    slope: Literal[1, 2, 3] | None = Field(default=None, description="Peak exercise ST slope")
    ca: int | None = Field(default=None, ge=0, le=3, description="Major vessels coloured (0 to 3)")
    thal: Literal[3, 6, 7] | None = Field(default=None, description="Thallium test result")

    @model_validator(mode="after")
    def require_minimum_measurements(self) -> Self:
        provided = sum(value is not None for value in self.model_dump().values())
        if provided < MIN_PROVIDED_FEATURES:
            raise ValueError(
                f"At least {MIN_PROVIDED_FEATURES} of {len(FEATURES)} measurements are "
                f"required; {provided} provided."
            )
        return self


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    model_name: Literal["random_forest", "logistic_regression"] = "random_forest"
    patient: PatientInput


class ContributionOut(BaseModel):
    feature: str
    label: str
    value: float | None = Field(description="Value as entered; null when it was missing")
    imputed: bool = Field(description="True when the model had to fill this input in")
    contribution: float = Field(description="Positive pushes toward disease, negative away")


class ExplanationOut(BaseModel):
    method: Literal["shap", "lime"]
    output_space: Literal["probability", "log_odds"]
    base_value: float | None = Field(description="SHAP only: output when no feature is known")
    fidelity: float | None = Field(description="LIME only: R2 of the local surrogate model")
    low_confidence: bool = Field(description="True when the explanation is a weak local fit")
    contributions: list[ContributionOut] = Field(description="Largest absolute effect first")


class AgreementOut(BaseModel):
    rank_correlation: float | None
    top_k_overlap: float
    sign_agreement: float
    k: int


class FeatureImpactOut(BaseModel):
    feature: str
    label: str
    probability_min: float = Field(description="Lowest probability while only this feature varies")
    probability_max: float = Field(description="Highest probability while only this feature varies")
    typical_low: float = Field(description="10th percentile while only this feature varies")
    typical_high: float = Field(description="90th percentile while only this feature varies")
    can_flip: bool = Field(
        description="True when typical values for this feature alone straddle the threshold"
    )


class SensitivityOut(BaseModel):
    """How much the result could change if the missing inputs took values real patients have."""

    baseline_probability: float = Field(
        description="Probability with missing inputs filled by typical training values"
    )
    probability_min: float = Field(description="Lowest probability over all training patterns")
    probability_max: float = Field(description="Highest probability over all training patterns")
    typical_low: float = Field(description="10th percentile over training patterns")
    typical_high: float = Field(description="90th percentile over training patterns")
    positive_share: float = Field(
        description="Share of plausible cases at or above the decision threshold"
    )
    verdict_uncertain: bool = Field(
        description="True when plausible cases disagree about the verdict "
        "(positive share between 10% and 90%)"
    )
    patterns_used: int = Field(description="Number of training patients that supplied values")
    impacts: list[FeatureImpactOut] = Field(description="Missing features, most influential first")
    note: str


class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    model_version: str
    probability: float = Field(description="Predicted probability of heart disease")
    threshold: float
    predicted_positive: bool
    calibrated: bool
    imputed_features: list[str]
    warnings: list[str]
    shap: ExplanationOut
    lime: ExplanationOut
    agreement: AgreementOut
    sensitivity: SensitivityOut | None = Field(
        default=None,
        description="Present only when some inputs were missing",
    )
    disclaimer: str


class OptionOut(BaseModel):
    value: int
    label: str


class FeatureSpecOut(BaseModel):
    name: str
    label: str
    kind: Literal["number", "category"]
    description: str
    unit: str | None
    minimum: float | None
    maximum: float | None
    options: list[OptionOut]


class ModelInfo(BaseModel):
    name: str
    role: Literal["primary", "glass_box_reference"]
    description: str


class ModelsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_version: str
    primary: str
    models: list[ModelInfo]
