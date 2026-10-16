"""Turns a validated patient into a diabetes prediction with explanations."""

import pandas as pd

from app.domain.diabetes_features import LABELS
from app.schemas.diabetes import (
    ContributionOut,
    DiabetesAgreementOut,
    DiabetesPatientInput,
    DiabetesPredictionRequest,
    DiabetesPredictionResponse,
    ExplanationOut,
    FeatureImpactOut,
    SensitivityOut,
)
from app.services.diabetes_registry import DiabetesModelRegistry
from ml.config import DECISION_THRESHOLD
from ml.explain import Explanation, compare
from ml.pipelines.diabetes import (
    FEATURES as DIABETES_FEATURES,
)
from ml.pipelines.diabetes import (
    SUSPICIOUS_ZERO_FEATURES,
)
from ml.sensitivity import SensitivityResult

LOW_FIDELITY_THRESHOLD = 0.5
DISCLAIMER = (
    "Decision support and educational prototype only, not a medical diagnosis. "
    "Trained on historical benchmark data (Pima Indians Diabetes Database, 768 female "
    "patients >= 21 years) and not validated for clinical use. Predictions are raw, "
    "uncalibrated machine learning outputs and must not be used for diagnosis or treatment."
)
SENSITIVITY_NOTE = (
    "Missing inputs are unknown, not normal. Contributions marked imputed are assumptions, "
    "not evidence. Ranges come from the values that real training patients have for the "
    "missing measurements; they describe the training population and do not take the "
    "entered measurements into account."
)


def patient_frame(patient: DiabetesPatientInput) -> pd.DataFrame:
    """One-row frame in model feature order; missing measurements become NaN."""
    return pd.DataFrame([patient.model_dump()], columns=DIABETES_FEATURES).astype(float)


def _explanation_out(explanation: Explanation) -> ExplanationOut:
    fidelity = explanation.fidelity
    return ExplanationOut(
        method=explanation.method,
        output_space=explanation.output_space,
        base_value=explanation.base_value,
        fidelity=fidelity,
        low_confidence=fidelity is not None and fidelity < LOW_FIDELITY_THRESHOLD,
        contributions=[
            ContributionOut(
                feature=item.feature,
                label=LABELS[item.feature],
                value=item.value,
                imputed=item.imputed,
                contribution=item.contribution,
            )
            for item in explanation.contributions
        ],
    )


def _sensitivity_out(result: SensitivityResult) -> SensitivityOut:
    return SensitivityOut(
        baseline_probability=result.baseline_probability,
        probability_min=result.probability_min,
        probability_max=result.probability_max,
        typical_low=result.typical_low,
        typical_high=result.typical_high,
        positive_share=result.positive_share,
        verdict_uncertain=result.verdict_uncertain,
        patterns_used=result.patterns_used,
        impacts=[
            FeatureImpactOut(
                feature=item.feature,
                label=LABELS[item.feature],
                probability_min=item.probability_min,
                probability_max=item.probability_max,
                typical_low=item.typical_low,
                typical_high=item.typical_high,
                can_flip=item.can_flip,
            )
            for item in result.impacts
        ],
        note=SENSITIVITY_NOTE,
    )


def sensitivity_warning(result: SensitivityResult) -> str | None:
    """A warning naming the most influential missing input, only when plausible cases
    disagree about the verdict."""
    if not result.verdict_uncertain or not result.impacts:
        return None
    lead = result.impacts[0]
    return (
        "The result is uncertain because of missing measurements: about "
        f"{result.positive_share:.0%} of plausible cases are positive. The most influential "
        f"is {LABELS[lead.feature]}, typically ranging from {lead.typical_low:.2f} "
        f"to {lead.typical_high:.2f}."
    )


def _range_warnings(frame: pd.DataFrame, ranges: dict[str, tuple[float, float]]) -> list[str]:
    warnings = []
    for feature in DIABETES_FEATURES:
        value = frame.iloc[0][feature]
        if pd.notna(value) and not (feature in SUSPICIOUS_ZERO_FEATURES and float(value) == 0.0):
            low, high = ranges[feature]
            if not low <= value <= high:
                warnings.append(
                    f"{LABELS[feature]} = {value:g} is outside the range seen in training data "
                    f"({low:g} to {high:g}); the prediction may be unreliable."
                )
    return warnings


def _suspicious_zero_warnings(frame: pd.DataFrame) -> list[str]:
    warnings = []
    for feature in SUSPICIOUS_ZERO_FEATURES:
        value = frame.iloc[0][feature]
        if pd.notna(value) and float(value) == 0.0:
            warnings.append(
                f"{LABELS[feature]} was entered as 0, which represents unmeasured data in this "
                "benchmark; it was imputed using the training median."
            )
    return warnings


class DiabetesPredictionService:
    def __init__(self, registry: DiabetesModelRegistry) -> None:
        self._registry = registry

    def predict(self, request: DiabetesPredictionRequest) -> DiabetesPredictionResponse:
        loaded = self._registry.get(request.model_name)
        frame = patient_frame(request.patient)

        shap_result = loaded.shap.explain(frame)
        lime_result = loaded.lime.explain(frame)
        probability = shap_result.probability

        warnings = _range_warnings(frame, self._registry.training_ranges)
        warnings.extend(_suspicious_zero_warnings(frame))

        sensitivity = loaded.sensitivity.analyze(frame)
        if sensitivity is not None:
            uncertainty_warning = sensitivity_warning(sensitivity)
            if uncertainty_warning is not None:
                warnings.append(uncertainty_warning)

        if request.model_name == "logistic_regression":
            agreement = None
            warnings.append(
                "Cross-explainer agreement metrics are omitted for logistic regression because "
                "SHAP operates in log-odds space while LIME operates in probability space."
            )
        else:
            raw_agreement = compare(shap_result, lime_result, k=3)
            agreement = DiabetesAgreementOut(
                rank_correlation=raw_agreement.rank_correlation,
                top_k_overlap=raw_agreement.top_k_overlap,
                sign_agreement=raw_agreement.sign_agreement,
                k=raw_agreement.k,
            )

        imputed_features = [
            f
            for f in DIABETES_FEATURES
            if pd.isna(frame.iloc[0][f])
            or (f in SUSPICIOUS_ZERO_FEATURES and float(frame.iloc[0][f]) == 0.0)
        ]

        return DiabetesPredictionResponse(
            model_name=request.model_name,
            model_version=self._registry.version,
            probability=probability,
            threshold=DECISION_THRESHOLD,
            predicted_positive=probability >= DECISION_THRESHOLD,
            calibrated=False,
            imputed_features=imputed_features,
            warnings=warnings,
            shap=_explanation_out(shap_result),
            lime=_explanation_out(lime_result),
            agreement=agreement,
            sensitivity=None if sensitivity is None else _sensitivity_out(sensitivity),
            disclaimer=DISCLAIMER,
        )
